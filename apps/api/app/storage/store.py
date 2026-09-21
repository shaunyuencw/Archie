import json, os, sqlite3
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
            CREATE TABLE IF NOT EXISTS changes(id TEXT PRIMARY KEY,project_id TEXT,body TEXT,state TEXT);
            CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,project_id TEXT,before TEXT,after TEXT,undone INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS requests(project_id TEXT,request_id TEXT,result TEXT,PRIMARY KEY(project_id,request_id));
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,project_id TEXT,status TEXT,result TEXT);
            CREATE TABLE IF NOT EXISTS usage(id TEXT PRIMARY KEY,project_id TEXT,action_id TEXT,day TEXT,provider TEXT,model TEXT,status TEXT,reserved REAL,cost REAL,details TEXT);
            CREATE TABLE IF NOT EXISTS cache(hash TEXT PRIMARY KEY,body TEXT);
            ''')
            db.execute("UPDATE runs SET status='interrupted' WHERE status='running'")
    def connect(self):
        db=sqlite3.connect(self.path,timeout=30); db.row_factory=sqlite3.Row
        return db
    def get(self,pid,db=None):
        if db is None:
            with self.connect() as db: return self.get(pid,db)
        row=db.execute('SELECT snapshot FROM projects WHERE id=?',(pid,)).fetchone()
        if not row: raise DomainError('not_found','Project not found',404)
        return Project.model_validate_json(row[0])
    def create(self,p):
        from ..domain.views import initialise_views
        p=initialise_views(p)
        with self.connect() as db: db.execute('INSERT INTO projects VALUES(?,?)',(p.id,p.model_dump_json()))
        return p
    def list(self):
        with self.connect() as db: return [{'id':p.id,'name':p.name,'revision':p.revision} for row in db.execute('SELECT snapshot FROM projects') for p in [Project.model_validate_json(row[0])]]
    def preview(self,c):
        p=self.get(c.project_id); apply(p,c)
        c.affected_ids=list(dict.fromkeys(o.id for o in c.operations if o.id))
        with self.connect() as db: db.execute('INSERT INTO changes VALUES(?,?,?,?)',(c.id,c.project_id,c.model_dump_json(),'pending'))
        return c
    def change(self,ident):
        with self.connect() as db:
            row=db.execute('SELECT body,state FROM changes WHERE id=?',(ident,)).fetchone()
        if not row: raise DomainError('not_found','Change not found',404)
        return ChangeSet.model_validate_json(row[0]).model_copy(update={'state':row[1]})
    def reject(self,ident):
        with self.connect() as db: db.execute("UPDATE changes SET state='rejected' WHERE id=? AND state='pending'",(ident,))
    def commit(self,c):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            prior=db.execute('SELECT result FROM requests WHERE project_id=? AND request_id=?',(c.project_id,c.request_id)).fetchone()
            if prior: return Project.model_validate_json(prior[0])
            p=self.get(c.project_id,db); result=apply(p,c)
            db.execute('UPDATE projects SET snapshot=? WHERE id=?',(result.model_dump_json(),p.id))
            db.execute('INSERT INTO history(project_id,before,after) VALUES(?,?,?)',(p.id,p.model_dump_json(),result.model_dump_json()))
            db.execute('DELETE FROM history WHERE project_id=? AND seq NOT IN (SELECT seq FROM history WHERE project_id=? ORDER BY seq DESC LIMIT 60)',(p.id,p.id))
            db.execute('INSERT INTO requests VALUES(?,?,?)',(p.id,c.request_id,result.model_dump_json()))
            db.execute("UPDATE changes SET state='accepted' WHERE id=?",(c.id,))
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
