export default function AssistantGreeting({busy,ready}:{busy:boolean,ready:boolean}){
 return <div className="assistant-intro"><img src="/brand/archie-assistant.png" alt="Archie, your friendly robot architecture assistant"/><div><h2>Ask Archie <span>:3</span></h2><p aria-live="polite">{busy?'Working on your next step...':ready?'Your changes are ready to review.':"Let's turn your requirements into a first draft."}</p></div></div>;
}
