import json, os, sqlite3
from contextlib import contextmanager
from pathlib import Path
from ..domain.models import Project, ChangeSet, now, uid
from ..domain.commands import apply, DomainError

class Store:
    def __init__(self,path=None):
        self.path=str(path or os.getenv('APP_DB','data/workbench.sqlite'))
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, snapshot TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS project_trash(project_id TEXT PRIMARY KEY, deleted_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS changes(id TEXT PRIMARY KEY,project_id TEXT,body TEXT,state TEXT);
            CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,before TEXT,after TEXT,undone INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS requests(project_id TEXT,request_id TEXT,result TEXT,PRIMARY KEY(project_id,request_id));
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,project_id TEXT,status TEXT,result TEXT);
            CREATE TABLE IF NOT EXISTS jobs(
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                request TEXT NOT NULL,
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                finished_at TEXT,
                dismissed_at TEXT,
                cancel_requested_at TEXT
            );
            CREATE INDEX IF NOT EXISTS jobs_recent ON jobs(created_at DESC);
            CREATE TABLE IF NOT EXISTS usage(id TEXT PRIMARY KEY,project_id TEXT,action_id TEXT,day TEXT,provider TEXT,model TEXT,status TEXT,reserved REAL,cost REAL,details TEXT);
            CREATE TABLE IF NOT EXISTS cache(hash TEXT PRIMARY KEY,body TEXT);
            ''')
            # Existing workbenches may already have the first background-job
            # schema.  Add cancellation without dropping their job history.
            columns={row[1] for row in db.execute('PRAGMA table_info(jobs)')}
            if 'cancel_requested_at' not in columns:
                db.execute('ALTER TABLE jobs ADD COLUMN cancel_requested_at TEXT')
            active_index=db.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='jobs_one_active_project'").fetchone()
            if not active_index or 'cancelling' not in (active_index[0] or ''):
                db.execute('DROP INDEX IF EXISTS jobs_one_active_project')
                db.execute("CREATE UNIQUE INDEX jobs_one_active_project ON jobs(project_id) WHERE status IN ('queued','running','cancelling')")
            db.execute("UPDATE runs SET status='interrupted' WHERE status='running'")
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=30); db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    def get(self,pid,db=None,include_trashed=False):
        if db is None:
            with self.connect() as db: return self.get(pid,db,include_trashed)
        row=db.execute('''SELECT projects.snapshot, project_trash.deleted_at FROM projects
                          LEFT JOIN project_trash ON projects.id=project_trash.project_id
                          WHERE projects.id=?''',(pid,)).fetchone()
        if not row: raise DomainError('not_found','Project not found',404)
        if row['deleted_at'] and not include_trashed:
            raise DomainError('project_trashed','This project is in Trash. Restore it before opening or editing.',404)
        return Project.model_validate_json(row[0])
    def create(self,p):
        from ..domain.views import initialise_views
        p=initialise_views(p)
        with self.connect() as db: db.execute('INSERT INTO projects VALUES(?,?)',(p.id,p.model_dump_json()))
        return p
    def list(self):
        with self.connect() as db:
            return [{'id':p.id,'name':p.name,'revision':p.revision} for row in db.execute('''SELECT snapshot FROM projects
                       WHERE NOT EXISTS (SELECT 1 FROM project_trash WHERE project_trash.project_id=projects.id)''')
                    for p in [Project.model_validate_json(row[0])]]
    def list_trash(self):
        with self.connect() as db:
            return [{'id':p.id,'name':p.name,'revision':p.revision,'deleted_at':row['deleted_at']}
                    for row in db.execute('''SELECT projects.snapshot, project_trash.deleted_at FROM project_trash
                        JOIN projects ON projects.id=project_trash.project_id ORDER BY deleted_at DESC''')
                    for p in [Project.model_validate_json(row['snapshot'])]]
    def _job_body(self,row,db):
        result=json.loads(row['result']) if row['result'] else None
        if isinstance(result,dict) and isinstance(result.get('proposal'),dict):
            proposal=result['proposal'];ident=proposal.get('id')
            if ident:
                change=db.execute('SELECT body,state FROM changes WHERE id=?',(ident,)).fetchone()
                if change:
                    proposal=json.loads(change['body']);proposal['state']=change['state']
                    result={**result,'proposal':proposal}
        snapshot=row['snapshot'] if 'snapshot' in row.keys() else None
        name=Project.model_validate_json(snapshot).name if snapshot else None
        return {'id':row['id'],'project_id':row['project_id'],'project_name':name,'kind':row['kind'],'status':row['status'],
                'request':json.loads(row['request']),'result':result,'error':json.loads(row['error']) if row['error'] else None,
                'created_at':row['created_at'],'started_at':row['started_at'],'finished_at':row['finished_at'],'dismissed_at':row['dismissed_at'],
                'cancel_requested_at':row['cancel_requested_at']}
    def create_job(self,pid,kind,request):
        if kind not in ['prompt','source','continue','policy_review']:raise DomainError('invalid_input','Unknown background job kind')
        ident=uid();created=now()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE');self.get(pid,db)
            active=db.execute("SELECT id FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling')",(pid,)).fetchone()
            if active:raise DomainError('job_active','This project already has a background action in progress.',409)
            queued=db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running','cancelling')").fetchone()[0]
            if queued>=8:raise DomainError('job_busy','ARCHIE is already processing eight background actions. Wait for one to finish, then try again.',409)
            try:db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(ident,pid,kind,'queued',json.dumps(request,separators=(',',':')),None,None,created,None,None,None,None))
            except sqlite3.IntegrityError as error:raise DomainError('job_active','This project already has a background action in progress.',409) from error
            row=db.execute('SELECT jobs.*,projects.snapshot FROM jobs JOIN projects ON jobs.project_id=projects.id WHERE jobs.id=?',(ident,)).fetchone()
            return self._job_body(row,db)
    def start_job(self,ident):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT project_id,status FROM jobs WHERE id=?',(ident,)).fetchone()
            if not row or row['status']!='queued':return False
            self.get(row['project_id'],db)
            db.execute("UPDATE jobs SET status='running',started_at=? WHERE id=? AND status='queued'",(now(),ident))
            return True
    def complete_job(self,ident,result):
        def encode(value):
            if hasattr(value,'model_dump'):return value.model_dump(mode='json')
            raise TypeError('Background result is not serializable')
        body=json.dumps(result,default=encode,separators=(',',':'))
        proposal_id=self._job_proposal_id(result)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT project_id,status FROM jobs WHERE id=?',(ident,)).fetchone()
            if not row:return
            if row['status']=='cancelling':
                if proposal_id:
                    db.execute("UPDATE changes SET state='rejected' WHERE id=? AND state='pending'",(proposal_id,))
                    self._remember_discarded_proposal(db,ident,proposal_id)
                db.execute("UPDATE jobs SET status='cancelled',result=NULL,error=NULL,finished_at=? WHERE id=? AND status='cancelling'",(now(),ident))
                return
            if row['status']!='running':return
            self.get(row['project_id'],db)
            db.execute("UPDATE jobs SET status='completed',result=?,error=NULL,finished_at=? WHERE id=? AND status='running'",(body,now(),ident))
    def fail_job(self,ident,error):
        body=json.dumps({'code':error.get('code','provider_output'),'message':error.get('message','Background processing failed.')},separators=(',',':'))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status FROM jobs WHERE id=?',(ident,)).fetchone()
            if not row:return
            if row['status']=='cancelling':
                db.execute("UPDATE jobs SET status='cancelled',result=NULL,error=NULL,finished_at=? WHERE id=? AND status='cancelling'",(now(),ident))
            elif row['status'] in ['queued','running']:
                db.execute("UPDATE jobs SET status='failed',error=?,finished_at=? WHERE id=? AND status IN ('queued','running')",(body,now(),ident))
    def request_job_cancel(self,ident):
        """Persist a cancellation request before signalling the worker thread."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status FROM jobs WHERE id=?',(ident,)).fetchone()
            if not row:raise DomainError('not_found','Background job not found',404)
            if row['status']=='queued':
                db.execute("UPDATE jobs SET status='cancelled',result=NULL,error=NULL,cancel_requested_at=COALESCE(cancel_requested_at,?),finished_at=? WHERE id=? AND status='queued'",(now(),now(),ident))
            elif row['status'] in ['running','cancelling']:
                db.execute("UPDATE jobs SET status='cancelling',cancel_requested_at=COALESCE(cancel_requested_at,?) WHERE id=? AND status IN ('running','cancelling')",(now(),ident))
            return self.get_job(ident,db)
    def _job_proposal_id(self,result):
        proposal=result.get('proposal') if isinstance(result,dict) else None
        if hasattr(proposal,'id'):return proposal.id
        if isinstance(proposal,dict) and isinstance(proposal.get('id'),str):return proposal['id']
        return None
    def _remember_discarded_proposal(self,db,ident,proposal_id):
        row=db.execute('SELECT request FROM jobs WHERE id=?',(ident,)).fetchone()
        if not row:return
        request=json.loads(row['request'])
        request['discarded_proposal_id']=proposal_id
        db.execute('UPDATE jobs SET request=? WHERE id=?',(json.dumps(request,separators=(',',':')),ident))
    def finish_job_cancelled(self,ident,result=None):
        """Make an acknowledged cancellation terminal without retaining late output."""
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            proposal_id=self._job_proposal_id(result)
            if proposal_id:
                db.execute("UPDATE changes SET state='rejected' WHERE id=? AND state='pending'",(proposal_id,))
                self._remember_discarded_proposal(db,ident,proposal_id)
            db.execute("UPDATE jobs SET status='cancelled',result=NULL,error=NULL,cancel_requested_at=COALESCE(cancel_requested_at,?),finished_at=? WHERE id=? AND status IN ('queued','running','cancelling')",(now(),now(),ident))
    def job_cancellation_requested(self,ident,db=None):
        if db is None:
            with self.connect() as db:return self.job_cancellation_requested(ident,db)
        row=db.execute('SELECT status,cancel_requested_at FROM jobs WHERE id=?',(ident,)).fetchone()
        return not row or row['status'] in ['cancelling','cancelled'] or row['cancel_requested_at'] is not None
    def ensure_job_running(self,ident,db):
        if self.job_cancellation_requested(ident,db):
            raise DomainError('cancelled','This background action was cancelled before it could save a result.',409)
        row=db.execute('SELECT status FROM jobs WHERE id=?',(ident,)).fetchone()
        if not row or row['status']!='running':
            raise DomainError('cancelled','This background action is no longer active and cannot save a result.',409)
    def get_job(self,ident,db=None):
        if db is None:
            with self.connect() as db:return self.get_job(ident,db)
        row=db.execute('SELECT jobs.*,projects.snapshot FROM jobs JOIN projects ON jobs.project_id=projects.id WHERE jobs.id=?',(ident,)).fetchone()
        if not row:raise DomainError('not_found','Background job not found',404)
        return self._job_body(row,db)
    def list_jobs(self,limit=100):
        with self.connect() as db:
            rows=db.execute('''SELECT jobs.*,projects.snapshot FROM jobs JOIN projects ON jobs.project_id=projects.id
                             WHERE jobs.dismissed_at IS NULL
                             ORDER BY CASE WHEN jobs.status IN ('queued','running','cancelling') THEN 0 ELSE 1 END, jobs.created_at DESC LIMIT ?''',(min(max(1,limit),100),)).fetchall()
            return [self._job_body(row,db) for row in rows]
    def dismiss_job(self,ident):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT status FROM jobs WHERE id=?',(ident,)).fetchone()
            if not row:raise DomainError('not_found','Background job not found',404)
            if row['status'] in ['queued','running','cancelling']:raise DomainError('job_active','A background action cannot be dismissed while it is running.',409)
            db.execute('UPDATE jobs SET dismissed_at=COALESCE(dismissed_at,?) WHERE id=?',(now(),ident))
            return self.get_job(ident,db)
    def recover_jobs(self):
        error=json.dumps({'code':'job_interrupted','message':'ARCHIE restarted before this background action finished. It was not replayed.'},separators=(',',':'))
        with self.connect() as db:
            result=db.execute("UPDATE jobs SET status='failed',error=?,finished_at=? WHERE status IN ('queued','running','cancelling')",(error,now()))
            return result.rowcount
    def trash(self,pid):
        # Lifecycle metadata is separate from the accepted architecture and its history.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            p=self.get(pid,db,include_trashed=True)
            db.execute('INSERT OR IGNORE INTO project_trash VALUES(?,?)',(pid,now()))
            deleted_at=db.execute('SELECT deleted_at FROM project_trash WHERE project_id=?',(pid,)).fetchone()[0]
            return {'id':p.id,'name':p.name,'deleted_at':deleted_at}
    def restore(self,pid):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            p=self.get(pid,db,include_trashed=True)
            db.execute('DELETE FROM project_trash WHERE project_id=?',(pid,))
            return p
    def empty_trash(self,project_ids):
        requested=list(dict.fromkeys(project_ids))
        if not requested:return {'deleted_ids':[],'deleted_count':0}
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            placeholders=','.join('?' for _ in requested)
            ids=[row[0] for row in db.execute(f'''SELECT project_id FROM project_trash
                     WHERE project_id IN ({placeholders})''',requested)]
            if not ids:return {'deleted_ids':[],'deleted_count':0}
            selected=set(ids);placeholders=','.join('?' for _ in ids)
            if db.execute(f"SELECT 1 FROM runs WHERE project_id IN ({placeholders}) AND status='running' LIMIT 1",ids).fetchone() or db.execute(f"SELECT 1 FROM jobs WHERE project_id IN ({placeholders}) AND status IN ('queued','running','cancelling') LIMIT 1",ids).fetchone():
                raise DomainError('project_busy','A project in Trash still has a running action. Wait for it to finish before emptying Trash.',409)
            orphan_candidates=set();surviving_sources=set()
            # Source extraction is cached by content hash and can be shared with other
            # projects. Keep hashes referenced by any surviving snapshot or undo state.
            for query in ['SELECT id AS project_id,snapshot AS body FROM projects',
                          'SELECT project_id,before AS body FROM history',
                          'SELECT project_id,after AS body FROM history',
                          'SELECT project_id,result AS body FROM requests']:
                for row in db.execute(query):
                    body=json.loads(row['body']);hashes=set()
                    for source in body.get('sources',[]):
                        if source.get('sha256'):hashes.add(source['sha256'])
                        hashes.update(source.get('variants',[]))
                    (orphan_candidates if row['project_id'] in selected else surviving_sources).update(hashes)
            cache_keys=orphan_candidates-surviving_sources
            for row in db.execute('SELECT hash,body FROM cache'):
                key=row['hash']
                # Imported IDs may themselves contain colons or SQL wildcards.
                # Narrative keys end in a revision; review bodies record ownership.
                if key.startswith(('narrative:','narrative-v2:')):
                    owner=key.split(':',1)[1].rpartition(':')[0]
                    if owner in selected:cache_keys.add(key)
                elif key.startswith('policy-review:'):
                    body=json.loads(row['body'])
                    if body.get('project_id') in selected:cache_keys.add(key)
            db.executemany('DELETE FROM cache WHERE hash=?',[(key,) for key in cache_keys])
            for table in ['history','changes','requests','runs','jobs','project_trash']:
                db.execute(f'DELETE FROM {table} WHERE project_id IN ({placeholders})',ids)
            db.execute(f'DELETE FROM projects WHERE id IN ({placeholders})',ids)
            # Usage and in-flight reservations remain: deleting a design must never
            # reset daily/project spending limits or erase the accounting record.
            return {'deleted_ids':ids,'deleted_count':len(ids)}
    def preview(self,c,job_id=None):
        c.affected_ids=list(dict.fromkeys(o.id for o in c.operations if o.id))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if job_id:self.ensure_job_running(job_id,db)
            p=self.get(c.project_id,db);apply(p,c)
            db.execute('INSERT INTO changes VALUES(?,?,?,?)',(c.id,c.project_id,c.model_dump_json(),'pending'))
        return c
    def change(self,ident):
        with self.connect() as db:
            row=db.execute('SELECT body,state FROM changes WHERE id=?',(ident,)).fetchone()
        if not row: raise DomainError('not_found','Change not found',404)
        return ChangeSet.model_validate_json(row[0]).model_copy(update={'state':row[1]})
    def reject(self,ident):
        with self.connect() as db: db.execute("UPDATE changes SET state='rejected' WHERE id=? AND state='pending'",(ident,))
    def commit(self,c,job_id=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if job_id:self.ensure_job_running(job_id,db)
            p=self.get(c.project_id,db)
            prior=db.execute('SELECT result FROM requests WHERE project_id=? AND request_id=?',(c.project_id,c.request_id)).fetchone()
            if prior: return Project.model_validate_json(prior[0])
            result=apply(p,c)
            # A new edit after undo starts a new branch; abandoned redo entries cannot replay.
            db.execute('DELETE FROM history WHERE project_id=? AND undone=1',(p.id,))
            db.execute('UPDATE projects SET snapshot=? WHERE id=?',(result.model_dump_json(),p.id))
            db.execute('INSERT INTO history(project_id,before,after) VALUES(?,?,?)',(p.id,p.model_dump_json(),result.model_dump_json()))
            db.execute('DELETE FROM history WHERE project_id=? AND seq NOT IN (SELECT seq FROM history WHERE project_id=? ORDER BY seq DESC LIMIT 60)',(p.id,p.id))
            db.execute('INSERT INTO requests VALUES(?,?,?)',(p.id,c.request_id,result.model_dump_json()))
            db.execute("UPDATE changes SET state='accepted',body=? WHERE id=?",(c.model_copy(update={'state':'accepted'}).model_dump_json(),c.id))
        return result
    def undo(self,c):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE'); p=self.get(c.project_id,db)
            apply(p,c) # verifies both semantic and presentation bases
            row=db.execute('SELECT * FROM history WHERE project_id=? AND undone=0 ORDER BY seq DESC LIMIT 1',(p.id,)).fetchone()
            if not row: raise DomainError('invalid_input','Nothing to undo')
            old=Project.model_validate_json(row['before'])
            old.revision=p.revision+1; old.updated_at=now()
            for k,v in old.views.items(): v.revision=p.views[k].revision+1
            db.execute('UPDATE projects SET snapshot=? WHERE id=?',(old.model_dump_json(),p.id))
            db.execute('UPDATE history SET undone=1 WHERE seq=?',(row['seq'],))
        return old
    def redo(self,c):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE'); p=self.get(c.project_id,db)
            apply(p,c)
            row=db.execute('SELECT * FROM history WHERE project_id=? AND undone=1 ORDER BY seq ASC LIMIT 1',(p.id,)).fetchone()
            if not row: raise DomainError('invalid_input','Nothing to redo')
            restored=Project.model_validate_json(row['after'])
            restored.revision=p.revision+1; restored.updated_at=now()
            for k,v in restored.views.items(): v.revision=p.views[k].revision+1
            db.execute('UPDATE projects SET snapshot=? WHERE id=?',(restored.model_dump_json(),p.id))
            db.execute('UPDATE history SET undone=0 WHERE seq=?',(row['seq'],))
        return restored
