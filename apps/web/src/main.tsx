import React from 'react';
import {createRoot} from 'react-dom/client';
import {ReactFlow, Background, Controls} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {Server} from 'lucide-react';
function App(){return <main style={{height:'95vh'}}><h1>Architecture Workbench · mock</h1><ReactFlow fitView nodes={[{id:'zone',type:'group',position:{x:0,y:0},data:{label:'Z1'},style:{width:400,height:250}},{id:'server',parentId:'zone',position:{x:50,y:80},data:{label:<><Server/> Management</>}},{id:'client',position:{x:500,y:80},data:{label:'Workstation'}}]} edges={[{id:'session',source:'client',target:'server',label:'management · protocol unknown'}]}><Background/><Controls/></ReactFlow></main>}
createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
