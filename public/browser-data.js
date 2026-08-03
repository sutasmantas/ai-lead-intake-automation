window.LEADDOCK_BROWSER_SEED = {
  leads: [
    {id:'lead_northstar',name:'Mira Chen',email:'mira@northstar.example',company:'Northstar Labs',need:'CRM and booking automation',qualification:{score:100,tier:'hot'},status:'needs_approval',crm:null,booking:null,handoff:null},
    {id:'lead_fieldnote',name:'Jon Bell',email:'jon@fieldnote.example',company:'Fieldnote',need:'lead intake integration',qualification:{score:83,tier:'hot'},status:'needs_approval',crm:null,booking:null,handoff:null},
    {id:'lead_orbit',name:'Asha Rao',email:'asha@orbit.example',company:'Orbit Studio',need:'website refresh',qualification:{score:28,tier:'cold'},status:'nurture',crm:null,booking:null,handoff:null},
    {id:'lead_retry',name:'Sam Rivera',email:'ops@retryworks.example',company:'Retry Works',need:'booking automation',qualification:{score:83,tier:'hot'},status:'needs_approval',crm:null,booking:null,handoff:null}
  ],
  availability: [
    {start:'2026-08-03T09:00:00+03:00',label:'Mon 03 Aug · 09:00'},
    {start:'2026-08-03T10:00:00+03:00',label:'Mon 03 Aug · 10:00'},
    {start:'2026-08-03T11:00:00+03:00',label:'Mon 03 Aug · 11:00'},
    {start:'2026-08-03T14:00:00+03:00',label:'Mon 03 Aug · 14:00'},
    {start:'2026-08-04T09:00:00+03:00',label:'Tue 04 Aug · 09:00'},
    {start:'2026-08-04T10:00:00+03:00',label:'Tue 04 Aug · 10:00'}
  ],
  bookings: [],
  dead_letters: [],
  audit: [
    {seq:1,event:'lead.accepted',subject:'lead_northstar',details:{score:100,tier:'hot'}},
    {seq:2,event:'lead.accepted',subject:'lead_fieldnote',details:{score:83,tier:'hot'}},
    {seq:3,event:'lead.accepted',subject:'lead_orbit',details:{score:28,tier:'cold'}},
    {seq:4,event:'lead.accepted',subject:'lead_retry',details:{score:83,tier:'hot'}}
  ]
};
