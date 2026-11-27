FIELDS = {
 'contacts': ('email','firstname','lastname','phone','jobtitle'),
 'companies': ('name','domain','phone','city','website'),
 'deals': ('dealname','amount','pipeline','dealstage','closedate'),
}
EXTERNAL_ID='salesgenie_external_id'
ALIASES={'contact':'contacts','company':'companies','deal':'deals','0-1':'contacts','0-2':'companies','0-3':'deals'}

def normalize(kind, properties, strict=False):
    if kind not in FIELDS: raise ValueError('Unsupported CRM object')
    if strict and set(properties)-set(FIELDS[kind]): raise ValueError('Unsupported CRM property')
    result={}
    for key in FIELDS[kind]:
        if key not in properties: continue
        value=properties[key]
        if value is None: result[key]=''
        elif isinstance(value,(str,int,float)) and not isinstance(value,bool): result[key]=str(value)
        else: raise ValueError('Properties must be strings, numbers or null')
    return result

def event_object(event):
    sub=event.get('subscriptionType') or event.get('eventType') or ''
    kind=ALIASES.get(event.get('objectTypeId')) or ALIASES.get(sub.split('.')[0])
    event_type=sub.split('.')[-1]
    if kind not in FIELDS or event_type not in ('creation','propertyChange','deletion','restore'): return None
    if event.get('objectId') is None: return None
    return kind,str(event['objectId'])
