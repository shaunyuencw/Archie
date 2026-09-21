export type PromptPack={scenario:string;provider_notes?:string;prompts:{prompt:string;provider?:string;expected?:string}[]};
export function parseImport(text:string):{kind:'prompts';pack:PromptPack}|{kind:'project';project:Record<string,unknown>}{
 let value:unknown;
 try{value=JSON.parse(text)}catch{throw new Error('This file is not valid JSON. Open an exported project, reusable pattern or follow-up prompt pack.');}
 if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Choose an ARCHIE project, pattern or follow-up prompt pack JSON file.');
 const data=value as Record<string,unknown>;
 if('prompts' in data||'scenario' in data){
  const validText=(value:unknown,max:number)=>typeof value==='string'&&value.trim().length>0&&value.length<=max;
  if(!validText(data.scenario,300)||!Array.isArray(data.prompts)||!data.prompts.length||data.prompts.length>50||
     (data.provider_notes!==undefined&&!validText(data.provider_notes,4000)))throw new Error('This prompt pack needs a scenario name and 1–50 prompts.');
  const prompts=data.prompts.map((entry:unknown)=>{
   if(!entry||typeof entry!=='object'||Array.isArray(entry))throw new Error('Each prompt pack entry needs prompt text.');
   const item=entry as Record<string,unknown>;
   if(!validText(item.prompt,12000)||['provider','expected'].some(key=>item[key]!==undefined&&!validText(item[key],4000)))throw new Error('Each entry needs prompt text and optional provider and expected-result notes.');
   return {prompt:item.prompt as string,provider:item.provider as string|undefined,expected:item.expected as string|undefined};
  });
  return {kind:'prompts',pack:{scenario:data.scenario as string,provider_notes:data.provider_notes as string|undefined,prompts}};
 }
 if(!Array.isArray(data.components)||!Array.isArray(data.interfaces))throw new Error('This JSON is not an exported ARCHIE project or a follow-up prompt pack.');
 return {kind:'project',project:data};
}
