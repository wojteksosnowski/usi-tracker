"use strict";(self.webpackChunkrp=self.webpackChunkrp||[]).push([["272"],{64164:function(e,t,r){e.exports=r.p+"e69a3716aeeb2374.svg"},15536:function(e,t,r){e.exports=r.p+"b096d0ce697e1473.svg"},22546:function(e,t,r){e.exports=r.p+"f0b6035c09869324.svg"},83176:function(e,t,r){e.exports=r.p+"1f70c688635d01bb.svg"},99335:function(e,t,r){e.exports=r.p+"0e742f41e124b6ec.svg"},54596:function(e,t,r){e.exports=r.p+"eb554d07ef4af330.svg"},40032:function(e,t,r){e.exports=r.p+"8cf038cce1c61381.svg"},43380:function(e,t,r){e.exports=r.p+"a7557d99d6c90511.svg"},83140:function(e,t,r){r.r(t),r.d(t,{useElementInteractionObserver:()=>i});var o=r(2784);let i=e=>{let t=(0,o.useRef)(null);return(0,o.useEffect)(()=>{let r=t.current;if(!r)return;let o=()=>{e.callback("click"),e.once&&r.removeEventListener("click",o,!0)},i=()=>{e.callback("scroll"),e.once&&r.removeEventListener("scroll",i,!0)},n=()=>{e.callback("touch"),e.once&&r.removeEventListener("touchstart",n,!0)};return r.addEventListener("click",o,!0),r.addEventListener("scroll",i,!0),r.addEventListener("touchstart",n,!0),()=>{null==r||r.removeEventListener("click",o,!0),null==r||r.removeEventListener("scroll",i,!0),null==r||r.removeEventListener("touchstart",n,!0)}},[]),t}},88703:function(e,t,r){r.r(t),r.d(t,{PlacesAutocomplete:()=>p});var o=r(52903),i=r(2784),n=r(28165),s=r(60338),a=r(41044),l=r(66278),c=r(70252),d=r(72422);function u(e,t,r,o,i,n,s){try{var a=e[n](s),l=a.value}catch(e){r(e);return}a.done?t(l):Promise.resolve(l).then(o,i)}let p=e=>{let{name:t,placeholder:r,labelContent:n,className:p}=e,[m,v,y]=(0,s.useField)(t),[h,g]=(0,i.useState)(""),b=m.value.value&&m.value.label,x=(0,i.useRef)(null),j=e.allowEditLastValue&&m.value.label&&m.value.value?[{label:m.value.label,value:m.value.value}]:void 0;return(0,o.jsxs)("div",{className:p,ref:x,children:[(0,o.jsx)(a.FieldWrapper,{message:v.error&&v.touched?v.error:"",fieldState:v.error&&v.touched?"error":"default",labelContent:n,children:(0,o.jsx)(l.SelectAsync,{disableDropdownIndicator:e.disableDropdownIndicator,inputValue:h,onInputChange:g,onMenuOpen:()=>{e.allowEditLastValue&&g(m.value.label||"")},defaultOptions:j,name:t,placeholder:r||"Lokalizacja",loadOptions:e=>(0,d.fetchDebouncedSearchGooglePlaces)(e,m.value),onChange:e=>{var t;return(t=function*(){yield(0,c.loadGoogleMapsApi)(["places"]);let t=document.getElementById("poiAutocomplete");new google.maps.places.PlacesService(t).getDetails({placeId:e.value},t=>{var r,o,i,n,s;if(t&&(null==t||null==(r=t.geometry)?void 0:r.location)){let r=null==(o=t.geometry)?void 0:o.location.lat(),a=null==(i=t.geometry)?void 0:i.location.lng();y.setValue((n=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},e),s=s={coordinates:[r,a]},Object.getOwnPropertyDescriptors?Object.defineProperties(n,Object.getOwnPropertyDescriptors(s)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(s)).forEach(function(e){Object.defineProperty(n,e,Object.getOwnPropertyDescriptor(s,e))}),n))}})},function(){var e=this,r=arguments;return new Promise(function(o,i){var n=t.apply(e,r);function s(e){u(n,o,i,s,a,"next",e)}function a(e){u(n,o,i,s,a,"throw",e)}s(void 0)})})()},value:b?m.value:void 0,noOptionsText:"Wpisz dokładny adres (np. Rodziny Hiszpańskich 8)"})}),(0,o.jsx)("div",{css:f,id:"poiAutocomplete"})]})},f=(0,n.css)`
    display: none;
`},60012:function(e,t,r){r.r(t),r.d(t,{PoiSwitcher:()=>O});var o=r(52903),i=r(2784),n=r(95397),s=r(7267),a=r(28165),l=r(89143),c=r(6511),d=r(39754),u=r(49111),p=r(83397),f=r(93148),m=r(30583),v=r(69011),y=r(86330),h=r(73916),g=r(29043),b=r(11646),x=r(29151);let j=[{type:b.PoiType.OFFERS,label:"Inwestycje"},{type:b.PoiType.TRANSPORT,label:"Komunikacja"},{type:b.PoiType.EDUCATION,label:"Edukacja"},{type:b.PoiType.SHOPS,label:"Sklepy"},{type:b.PoiType.SPORT,label:"Sport"},{type:b.PoiType.HEALTH,label:"Zdrowie"},{type:b.PoiType.ENTERTAINMENT,label:"Place zabaw"},{type:b.PoiType.FOOD,label:"Kawiarnie i restauracje"}],O=e=>{let t=(0,n.useDispatch)(),r=(0,s.useParams)(),[a,l]=(0,i.useState)(!1),c=(0,n.useSelector)(e=>e.viewType.current);return(0,o.jsxs)("div",{css:w,className:e.className,children:[e.hideHeader?null:(0,o.jsxs)("div",{css:S,children:[(0,o.jsx)(y.Text,{as:"span",variant:"headline_6",children:"Ważne miejsca"}),e.disableCollapsible?null:(0,o.jsx)("span",{css:_,onClick:()=>l(e=>!e),children:a?(0,o.jsx)(f.ChevronDownIcon,{size:"2"}):(0,o.jsx)(m.ChevronUpIcon,{size:"2"})})]}),(!a||e.disableCollapsible)&&(0,o.jsx)("div",{children:j.map(i=>{let n=e.checkedPoiTypes.includes(i.type);return(0,o.jsxs)("div",{css:[T],children:[(0,o.jsx)(y.Text,{variant:"info_txt_1",as:"span",children:i.label}),(0,o.jsx)(v.Switcher,{id:i.type,checked:n,onChange:o=>{var n;return n=i.type,void(t((0,h.setActivePoiDirections)(null)),e.onChange(o?e.checkedPoiTypes.concat(n):e.checkedPoiTypes.filter(e=>e!==n)),g.poiAnalytics.gtm.mapEvent({action:o?g.PoiGTMModalAction.IMPORTANT_PLACES_ON:g.PoiGTMModalAction.IMPORTANT_PLACES_OFF,label:P(n)}),g.poiAnalytics.algolytics.showPoi(c,o,n,r.offerId,r.propertyId))},labelContent:""})]},i.type)})}),e.onDistanceChange?(0,o.jsxs)("div",{css:k,children:[(0,o.jsx)(y.Text,{variant:"body_copy_2",strong:!0,mb:1,as:"div",children:"Promień"}),(0,o.jsx)(x.PoiSwitcherDistance,{value:e.distanceValue,onChange:e.onDistanceChange})]}):null]})},P=e=>e===b.PoiType.OFFERS?"investment":e,w=e=>(0,a.css)`
    background-color: #fff;
    width: 100%;

    @media (min-width: ${e.breakpoints.md}) {
        width: 26.4rem;
        ${(0,l.elevation)()};
        ${(0,c.borderRadius)(2)};
        ${(0,d.p)(2)};
    }
`,S=e=>(0,a.css)`
    ${(0,u.mt)(4)};
    ${(0,u.mb)(3)};
    ${(0,p.flex)("center","space-between")};
    user-select: none;

    @media (min-width: ${e.breakpoints.md}) {
        ${(0,u.mt)(0)};
    }
`,_=e=>(0,a.css)`
    cursor: pointer;

    @media (max-width: ${e.breakpoints.md}) {
        display: none;
    }
`,T=e=>(0,a.css)`
    user-select: none;
    ${(0,u.mb)(2)};
    ${(0,p.flex)("center","space-between")}

    &:last-of-type {
        ${(0,u.mb)(0)};
    }

    @media (max-width: ${e.breakpoints.md}) {
        margin-bottom: 2rem;
    }
`,k=(0,a.css)`
    ${(0,u.mt)(3)};
`},29151:function(e,t,r){r.r(t),r.d(t,{PoiSwitcherDistance:()=>l});var o=r(52903),i=r(2784),n=r(28165),s=r(50604),a=r(86557);let l=e=>{let{value:t,isBorderless:r,onChange:n}=e,l=(0,i.useRef)(null),u="number"!=typeof t?a.POI_DISTANCE_DEFAULT_VALUE:t,p=(0,i.useMemo)(()=>(e.options||a.poiDistanceSelectOptions).find(e=>e.value===u),[u,e.options]);return(0,o.jsx)("div",{css:c,ref:e=>{l.current=e},children:(0,o.jsx)(s.Select,{value:p,options:e.options||a.poiDistanceSelectOptions,name:"poi-distance",onChange:e=>{n(e.value)},isBorderless:r,css:d,menuPlacement:"top"})})},c=(0,n.css)`
    display: flex;
    flex-direction: row;
    align-items: center;
    width: 100%;
`,d=(0,n.css)`
    flex: 1 1 100%;
`},93068:function(e,t,r){r.r(t),r.d(t,{PoiTravelMode:()=>k});var o=r(52903),i=r(2784),n=r(95397),s=r(77605),a=r(30134),l=r(20016);let c=e=>{var t,r;return(0,o.jsx)(l.SvgIcon,(t=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},e),r=r={children:(0,o.jsx)("path",{d:"M6.025 1.211a.725.725 0 1 1-1.026 1.026.725.725 0 0 1 1.026-1.026ZM6.074 5.028l-.247-.543-.241-.534-.265 1.564.783.771V9h-.76V6.605l-.707-.695-.495 2.892-.21-.036h-.003l-.536-.09.884-5.16-.734.331v1.35H3v-1.7l1.384-.627.004-.002.478-.216.044.004.065.005.15.014.124.01.375.033.12.267.004.009.676 1.492h1.31v.543h-1.66Z"})},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t))};var d=r(45973),u=r(45706),p=r(73916),f=r(34978),m=r(29043),v=r(11646),y=r(28165),h=r(83397),g=r(6511),b=r(49111),x=r(86330);function j(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}let O=e=>{let{selected:t,travelMode:r,onClick:i,duration:n,className:s}=e,l={size:"1.6",fill:"#fff"};return(0,o.jsxs)("span",{css:P(t),onClick:i,className:s,children:[r===u.TravelMode.DRIVING&&(0,o.jsx)(a.CarOutlineIcon,j({},l)),r===u.TravelMode.WALKING&&(0,o.jsx)(c,j({},l)),r===u.TravelMode.TRANSIT&&(0,o.jsx)(d.PoiBusIcon,j({},l))," ",t&&n&&(0,o.jsx)(x.Text,{as:"span",strong:!0,variant:"info_txt_1",css:w,children:n})]})},P=e=>t=>(0,y.css)`
    width: 100%;
    height: 2.4rem;
    background-color: ${e?t.colors.primary:t.colors.gray[700]};
    cursor: pointer;
    ${h.flexAbsoluteCenter};
    ${(0,g.borderRadius)()};
    ${(0,b.mh)()};

    &:last-of-type,
    &:first-of-type {
        margin: 0;
    }

    & > svg {
        fill: ${e?t.colors.secondary:"#fff"};
    }
`,w=(0,y.css)`
    display: inline-block;
    margin-left: 1rem;
    white-space: pre;
`;function S(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}let _={size:"1.6",fill:"#fff"},T=[{mode:u.TravelMode.DRIVING,label:"Car",icon:(0,o.jsx)(a.CarOutlineIcon,S({},_))},{mode:u.TravelMode.WALKING,label:"Walk",icon:(0,o.jsx)(c,S({},_))},{mode:u.TravelMode.TRANSIT,label:"Bus",icon:(0,o.jsx)(d.PoiBusIcon,S({},_))}],k=e=>{let t=(0,n.useDispatch)(),{getPoiDirections:r}=(0,f.useGooglePoiTravelDirections)(),a=(0,n.useSelector)(e=>e.maps.travelDirections.activePoi),l=(0,n.useSelector)(e=>e.maps.travelDirections.activePoiDirections),c=(0,n.useSelector)(e=>{var t;return null==(t=e.offerDetail.offer)?void 0:t.id}),d=(0,n.useSelector)(e=>e.maps.travelDirections.poisDirections),y=(0,n.useSelector)(e=>{var t;return null==(t=e.property.property)?void 0:t.id}),h=(0,n.useSelector)(e=>e.viewType.current),[g,b]=(0,i.useState)({mode:null,duration:null});(0,i.useEffect)(()=>{t((0,p.setActivePoiDirections)(null)),b({mode:null,duration:null})},[e.poi.id,e.poi.distance]),(0,i.useEffect)(()=>{e.listenToActivePoiDirections&&(null==l?void 0:l.id)===e.poi.id&&b({mode:l.travelMode,duration:(0,u.formatDuration)(d[e.poi.id][l.travelMode].duration,"m")})},[e.listenToActivePoiDirections,l,d]),(0,i.useEffect)(()=>{e.poi.id===(null==a?void 0:a.id)&&e.calcTravelDataOnOpen&&x(u.TravelMode.DRIVING,!0)},[e.calcTravelDataOnOpen,e.poi.id,null==a?void 0:a.id,b]);let x=(o,i=!1)=>{if(i||m.poiAnalytics.gtm.mapEvent({action:e.poiType===v.PoiType.USER?m.PoiGTMModalAction.MY_POI_CALCULATE:m.PoiGTMModalAction.MAP_POI_CALCULATE,label:o}),d[e.poi.id]&&d[e.poi.id][o]){t((0,p.setActivePoiDirections)({id:e.poi.id,travelMode:o,poiType:e.poiType}));let r=(0,u.formatDuration)(d[e.poi.id][o].duration,"m")||"1 m";b({mode:o,duration:r}),i||m.poiAnalytics.algolytics.meansOfTransportClick(h,e.poiType,e.poi,o,parseInt(r),c,y);return}e.targetCoords&&r(e.poi,e.poiType,e.targetCoords,o).then(t=>{if(t){let r=(0,u.formatDuration)(t.duration,"m")||"1 m";b({mode:o,duration:r}),i||m.poiAnalytics.algolytics.meansOfTransportClick(h,e.poiType,e.poi,o,parseInt(r),c,y)}}).catch(console.log)};return(0,o.jsx)("div",{css:(0,s.display)("flex"),children:T.map(e=>(0,o.jsx)(O,{travelMode:e.mode,selected:g.mode===e.mode,onClick:()=>x(e.mode),duration:g.duration},e.mode))})}},91114:function(e,t,r){r.r(t),r.d(t,{PoiTravelModeInfoWindow:()=>O});var o=r(52903),i=r(2784),n=r(95397),s=r(98986),a=r(55851),l=r(49111),c=r(6291),d=r(86330),u=r(70278),p=r(52098),f=r(73916),m=r(84702),v=r(26588),y=r(11646),h=r(29043),g=r(29313),b=r(20318),x=r(93068),j=r(51966);let O=e=>{var t;let{onClose:r,poi:a,poiType:O}=e,_=function(e,t){if(null==e)return{};var r,o,i=function(e,t){if(null==e)return{};var r,o,i={},n=Object.keys(e);for(o=0;o<n.length;o++)r=n[o],t.indexOf(r)>=0||(i[r]=e[r]);return i}(e,t);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);for(o=0;o<n.length;o++)r=n[o],!(t.indexOf(r)>=0)&&Object.prototype.propertyIsEnumerable.call(e,r)&&(i[r]=e[r])}return i}(e,["onClose","poi","poiType"]),T=(0,n.useDispatch)(),{isMobile:k}=(0,u.useUserDevice)(),C=(0,n.useSelector)(e=>e.maps.travelDirections.activePoi),M=(0,n.useSelector)(e=>e.maps.travelDirections.activePoiRoute),I=(0,n.useSelector)(e=>{var t;return null==(t=e.offerDetail.offer)?void 0:t.id}),D=(0,n.useSelector)(e=>{var t;return null==(t=e.property.property)?void 0:t.id}),$=(0,n.useSelector)(e=>e.viewType.current);(0,i.useEffect)(()=>{e.calcTravelDataOnOpen||(h.poiAnalytics.gtm.mapEvent({action:h.PoiGTMModalAction.MAP_POI_CLICK,label:e.poiType}),h.poiAnalytics.algolytics.poiClick($,e.poiType,k&&C?C:a,I,D))},[e.poi,e.calcTravelDataOnOpen,C]);let{hasAnyPoiRoutes:A,poiRoutesGrouped:L}=((e,t)=>{let r=(0,n.useSelector)(e=>e.maps.poi.requestedArea),o=(0,n.useSelector)(e=>{var r;return null==(r=e.maps.poi.poisRoutes)?void 0:r[t]})||null,s=(0,n.useDispatch)(),a=(0,i.useMemo)(()=>o?o.reduce((e,t)=>(e[t.type]=(0,m.uniq)([...e[t.type]||[],t]),e),{}):null,[o]);return(0,i.useEffect)(()=>{(null==r?void 0:r.latitude)&&(null==r?void 0:r.longitude)&&e===y.PoiType.TRANSPORT&&s((0,v.fetchOsmPoiRoutes)({poiId:t}))},[r,t]),{poiRoutes:o,hasAnyPoiRoutes:!!(o&&o.length>0),poiRoutesGrouped:a}})(O,a.id);return k&&!C?null:(0,o.jsxs)("div",{className:P,children:[(0,o.jsx)("span",{className:w,onClick:()=>{null==r||r(),T((0,f.setActivePoiDirections)(null)),T((0,f.setActivePoi)(null,null))},children:(0,o.jsx)(c.CloseIcon,{size:"1.6"})}),(0,o.jsx)(d.Text,{as:"div",variant:"headline_6",children:a.name}),!!(null==a||null==(t=a.tags)?void 0:t.address)&&(0,o.jsx)("div",{className:(0,s.cx)(S,"bt"),children:a.tags.address}),A&&L?(0,o.jsxs)("div",{children:[(0,o.jsx)(d.Text,{as:"div",variant:"info_txt_2",css:[(0,l.mt)(2),(0,l.mb)(1)],children:"Komunikacja"}),(0,o.jsx)(j.RegionTransportRoutes,{busRoutes:null==L?void 0:L.bus,railwayRoutes:null==L?void 0:L.train,subwayRoutes:null==L?void 0:L.subway,tramRoutes:null==L?void 0:L.tram,activePoiRoute:M,onTransportRouteClick:e=>{T((0,f.setActivePoiRoute)(e.id===(null==M?void 0:M.id)?null:e)),e.type===b.IPublicTransportType.BUS?(0,g.hitGtmBusRouteClick)():(0,p.hitGoogleTagManager)({event:"map_poi_railroad"})}}),(0,o.jsx)(d.Text,{as:"div",variant:"info_txt_2",css:[(0,l.mt)(2),(0,l.mb)(1)],children:"Czas dojazdu"})]}):null,(0,o.jsx)("div",{css:(0,l.mt)(1),children:(0,o.jsx)(x.PoiTravelMode,function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({poi:a,poiType:O},_))})]})},P=(0,a.css)({backgroundColor:"#fff",position:"relative",minWidth:"24rem",borderRadius:2,padding:2,md:{paddingRight:1.5}}),w=(0,a.css)({position:"absolute",top:1,right:1,cursor:"pointer",md:{right:1}}),S=(0,a.css)({fontSize:"0.8rem",lineHeight:"1.8rem"})},51966:function(e,t,r){r.r(t),r.d(t,{RegionTransportRoutes:()=>S});var o=r(52903),i=r(2784),n=r(75264),s=r(28165),a=r(2859),l=r(77605),c=r(49111),d=r(67506),u=r(89289),p=r(7551),f=r(83397),m=r(94507),v=r(6511),y=r(39754),h=r(19922),g=r(51328),b=r(16830),x=r(45973),j=r(86330);let O=e=>(0,i.useMemo)(()=>(null==e?void 0:e.filter((t,r)=>(null==e?void 0:e.findIndex(e=>t.name===e.name))===r))||[],[e]),P={bus:"#9BD7FF",railway:"#BCAFE1",subway:"#FFCDA5",tram:"#B9E19B"},w=e=>`Od ${e.from} do ${e.to}`,S=e=>{let t=(0,n.u)(),[r,s]=(0,i.useState)(!1),p=(r,o)=>{let i;return(0,a.backgroundColor)((i=e.activePoiRoute,o&&i&&(null==o?void 0:o.id)===(null==i?void 0:i.id))?t.colors.primary:P[r])},f=O(e.busRoutes),m=(0,i.useMemo)(()=>null==f?void 0:f.sort((e,t)=>{let r="N"===e.name[0],o="N"===t.name[0];return r&&o||!r&&!o?0:r?1:-1}),[f]),v=O(e.subwayRoutes),y=O(e.tramRoutes),S=O(e.railwayRoutes),C=(null==v?void 0:v.length)||0,M=(null==S?void 0:S.length)||0,I=(null==y?void 0:y.length)||0,D=(null==m?void 0:m.length)||0,$={subway:0,railway:C,tram:C+M,bus:C+M+I},A=(e,t)=>r||$[e]+t<25?"":(0,l.display)("none");return(0,o.jsxs)("div",{children:[(0,o.jsxs)("ul",{css:_,children:[v.map((t,r)=>(0,o.jsxs)("li",{css:[T,p("subway",t),A("subway",r)],title:w(t),onClick:()=>e.onTransportRouteClick(t),children:[(0,o.jsx)(h.PoiSubwayIcon,{size:"2.4",wrapperSize:"2",wrapperColor:"transparent",css:[k]}),(0,o.jsx)(j.Text,{as:"span",variant:"info_txt_2",strong:!0,children:t.name})]},t.id)),S.map((t,r)=>(0,o.jsxs)("li",{css:[T,p("railway",t),A("railway",r)],title:w(t),onClick:()=>e.onTransportRouteClick(t),children:[(0,o.jsx)(g.PoiTrainIcon,{size:"1.6",wrapperSize:"2",wrapperColor:"transparent",css:[k]}),(0,o.jsx)(j.Text,{as:"span",variant:"info_txt_2",strong:!0,children:t.name})]},t.id)),y.map((t,r)=>(0,o.jsxs)("li",{css:[T,p("tram",t),A("tram",r)],title:w(t),onClick:()=>e.onTransportRouteClick(t),children:[(0,o.jsx)(b.PoiTramIcon,{size:"1.6",wrapperSize:"2",wrapperColor:"transparent",css:[k]}),(0,o.jsx)(j.Text,{as:"span",variant:"info_txt_2",strong:!0,children:t.name})]},t.id)),m.map((t,r)=>(0,o.jsxs)("li",{css:[T,p("bus",t),A("bus",r)],title:w(t),onClick:()=>e.onTransportRouteClick(t),children:[(0,o.jsx)(x.PoiBusIcon,{size:"1.6",wrapperSize:"2",wrapperColor:"transparent",css:[k]}),(0,o.jsx)(j.Text,{as:"span",variant:"info_txt_2",strong:!0,children:t.name})]},t.id))]}),C+M+I+D>25?(0,o.jsx)(j.Text,{as:"div",variant:"info_txt_1",css:[(0,c.mt)(1),d.underline,u.pointer],onClick:()=>{s(e=>!e)},children:r?"Pokaż mniej linii komunikacyjnych":"Pokaż więcej linii komunikacyjnych"}):null]})},_=(0,s.css)`
    ${p.listUnStyled};
    ${(0,f.flex)()};
    ${(0,c.m)(.5,0,0,0)};
    flex-wrap: wrap;
    gap: ${(0,m.calculateRemSize)(.5)};
`,T=(0,s.css)`
    ${(0,f.flex)("center","space-between")};
    ${(0,v.borderRadius)()};
    ${(0,y.ph)(1)};
    height: 2.4rem;
    cursor: pointer;
`,k=(0,s.css)`
    ${(0,y.pr)(1)};
`},89082:function(e,t,r){r.r(t),r.d(t,{OpenStreetMapsWithPoi:()=>eZ});var o=r(52903),i=r(2784),n=r(95397),s=r(75264),a=r(28165),l=r(92162),c=r(39754),d=r(49111),u=r(66770),p=r(25598),f=r(62749),m=r(37867),v=r(86330),y=r(28309),h=r(19743),g=r(46482),b=r(58398),x=r(90467),j=r(70278),O=r(35135),P=r(72979),w=r(76755),S=r(73916),_=r(71529),T=r(69751),k=r(64462),C=r(6291);let M=e=>(0,o.jsxs)("div",{css:I,children:[e.onClose&&(0,o.jsx)("span",{css:D,onClick:e.onClose,children:(0,o.jsx)(C.CloseIcon,{size:"1"})}),(0,o.jsx)("div",{css:[$],children:e.poiRoute.name}),(0,o.jsxs)("div",{children:["Od: ",e.poiRoute.from]}),(0,o.jsxs)("div",{children:["Do: ",e.poiRoute.to]})]}),I=(0,a.css)`
    background-color: #fff;
    border-radius: 0.4rem;
    padding: 2rem;
`,D=e=>(0,a.css)`
    position: absolute;
    top: 1rem;
    right: 1rem;
    cursor: pointer;

    @media (max-width: ${e.breakpoints.md}) {
        right: 1.5rem;
    }
`,$=(0,a.css)`
    font-size: 2.2rem;
    font-weight: 500;
`;var A=r(45056),L=r(78756),E=r(4523),R=r(34978),N=r(60680),z=r(46433),F=r(67108),V=r(11646),U=r(80990),G=r(68159);let B=r(15536),H=r(40032),W=r(99335),Z=r(22546),q=r(54596),K=r(83176),Q=r(43380);var Y=r(60957),X=r(6502),J=r(86557),ee=r(580),et=r(5562),er=r(64726);let eo=e=>{let t=()=>e.onModalClose(!0);return(0,o.jsxs)(er.Modal,{isOpen:e.modalState,onModalClose:t,children:[(0,o.jsx)(er.Modal.Header,{variant:"bar_mini",children:"Miejsca na mapie"}),(0,o.jsxs)(er.Modal.Content,{css:[(0,et.prettyScroll)(),(0,c.p)(0,4)],children:[e.children,(0,o.jsxs)("div",{children:[(0,o.jsx)(ee.Button,{css:[u.w100,(0,d.mt)()],variant:"filled_primary",onClick:()=>e.onModalClose(!1),children:"Zapisz"}),(0,o.jsx)(ee.Button,{css:[u.w100,(0,d.mt)()],variant:"none_secondary",onClick:t,children:"Anuluj"})]})]})]})};var ei=r(29043);let en=e=>((0,i.useEffect)(()=>{ei.poiAnalytics.gtm.mapEvent({action:ei.PoiGTMModalAction.MAP_INVESTMENT_MARKER_CLICK,label:"investment"})},[]),(0,o.jsxs)("div",{css:es,children:[e.onClose&&(0,o.jsx)("span",{css:ea,onClick:e.onClose,children:(0,o.jsx)(C.CloseIcon,{size:"1"})}),(0,o.jsx)("div",{css:el,className:"bt",children:e.offer.name}),(0,o.jsx)("div",{css:(0,d.mv)(),className:"bt",children:e.offer.address}),(0,o.jsx)("div",{className:"bt",children:e.offer.vendor.name})]})),es=(0,a.css)`
    background-color: #fff;
    border-radius: 0.4rem;
    padding: 2rem;
`,ea=e=>(0,a.css)`
    position: absolute;
    top: 1rem;
    right: 1rem;
    cursor: pointer;

    @media (max-width: ${e.breakpoints.md}) {
        right: 1.5rem;
    }
`,el=(0,a.css)`
    font-size: 2.2rem;
    font-weight: 500;
`;var ec=r(60012),ed=r(91114),eu=r(89143),ep=r(83397),ef=r(89289),em=r(6511),ev=r(93148),ey=r(30583),eh=r(55673),eg=r(7267),eb=r(60338),ex=r(48601),ej=r(41044),eO=r(31638),eP=r(96665),ew=r(85866),eS=r(88703);function e_(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}let eT={name:"",location:{label:"",value:"",coordinates:[]}},ek=ex.object({name:ex.string().required(eP.validationMessages.required),location:ex.mixed().test({message:eP.validationMessages.required,test:e=>(0,ew.isValidLocationObject)(e)})}),eC=e=>{let t=(0,n.useDispatch)(),{isMobile:r}=(0,j.useUserDevice)(),i=(0,eg.useParams)(),s=(0,n.useSelector)(e=>e.viewType.current);return(0,o.jsx)(eb.Formik,{initialValues:e_({},eT,e.formInitialValues),validationSchema:ek,onSubmit:(r,{resetForm:o,setSubmitting:n})=>{if(e.targetCoords){let{name:a,location:{label:l}}=r,{lat:c,lng:d}=(0,k.convertToLatLngLiteralOfPoland)(r.location.coordinates),{lng:u,lat:p}=(0,k.convertToLatLngLiteralOfPoland)(e.targetCoords),f=(0,T.countDistance)({lat:c,lng:d},{lat:p,lng:u}),m={id:Date.now(),distance:f,lat:c,lng:d,name:a,tags:{address:l}};e.formInitialValues?t((0,X.editUserPoi)(e.formInitialValues.location.value,m)):t((0,X.addUserPoi)(m)),n(!1),o(),ei.poiAnalytics.gtm.mapEvent({action:ei.PoiGTMModalAction.CREATE_MY_POI_SUBMIT,label:a}),ei.poiAnalytics.algolytics.addMyPoi(s,m,i.offerId,i.propertyId),e.onHideForm()}},enableReinitialize:!0,children:t=>(0,o.jsxs)("form",{onSubmit:t.handleSubmit,children:[(0,o.jsxs)("div",{children:[(0,o.jsx)("div",{css:(0,d.mb)(2),children:(0,o.jsx)(eb.Field,{name:"name",children:({field:e,meta:t})=>{var r,i;return(0,o.jsx)(ej.FieldWrapper,{message:t.error,fieldState:t.error&&t.touched?"error":"default",children:(0,o.jsx)(eO.Input,(r=e_({},e),i=i={placeholder:"Nazwa miejsca"},Object.getOwnPropertyDescriptors?Object.defineProperties(r,Object.getOwnPropertyDescriptors(i)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(i)).forEach(function(e){Object.defineProperty(r,e,Object.getOwnPropertyDescriptor(i,e))}),r))})}})}),(0,o.jsx)(eS.PlacesAutocomplete,{name:"location"})]}),(0,o.jsx)(ee.Button,{css:[u.w100,(0,d.mt)(2)],type:"submit",disabled:t.isSubmitting,variant:"filled_primary",children:r?"Dodaj miejsce":"Zapisz"}),!r&&(0,o.jsx)(ee.Button,{css:[u.w100,(0,d.mt)(2)],variant:"none_secondary",onClick:e.onHideForm,children:"Anuluj"})]})})};var eM=r(67545),eI=r(20016);let eD=e=>{var t,r;return(0,o.jsxs)(eI.SvgIcon,(t=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},e),r=r={children:[(0,o.jsx)("path",{d:"M6.3 1H3.633v.533H6.3V1ZM3.9 4.203h.533v3.194H3.9V4.203ZM5.5 4.203h.533v3.194H5.5V4.203Z"}),(0,o.jsx)("path",{fillRule:"evenodd",clipRule:"evenodd",d:"M1.5 3.137V1.538h6.933v1.595H7.9V9H2.033V3.137H1.5Zm1.067 5.33h4.8V3.133h-4.8v5.334ZM2.033 2.6H7.9v-.53H2.033v.53Z"})]},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t))};var e$=r(93068);function eA(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}let eL={fillColor:"#ccc",size:"1.4"},eE=e=>{let t=(0,n.useDispatch)(),r=(0,n.useSelector)(e=>e.maps.userPoi);return(0,o.jsx)(i.Fragment,{children:r.map(r=>(0,o.jsxs)("div",{css:eR,children:[(0,o.jsxs)("div",{css:eN,children:[(0,o.jsx)("div",{css:ez,children:(0,o.jsx)(v.Text,{as:"span",variant:"body_copy_2",children:r.name})}),(0,o.jsxs)("div",{children:[(0,o.jsx)("span",{css:[(0,d.ml)(3),ef.pointer],onClick:()=>e.onUserPoiEdit(r),children:(0,o.jsx)(eM.EditIcon,eA({},eL))}),(0,o.jsx)("span",{css:[(0,d.ml)(3),ef.pointer],onClick:()=>{var e,o;return e=r.id,o=r.name,void(t((0,X.removeUserPoi)(e)),t((0,S.setActivePoiDirections)(null)),ei.poiAnalytics.gtm.mapEvent({action:ei.PoiGTMModalAction.DELETE_MY_POI,label:o}))},children:(0,o.jsx)(eD,eA({},eL))})]})]}),(0,o.jsx)(e$.PoiTravelMode,{listenToActivePoiDirections:!0,poi:r,poiType:V.PoiType.USER,targetCoords:e.targetCoords})]},r.id))})},eR=e=>(0,a.css)`
    border-bottom: 1px solid ${e.colors.gray[300]};
    ${(0,c.pb)(2)};
    ${(0,d.mb)()};

    &:first-of-type {
        ${(0,d.mt)(3)};
    }

    &:last-of-type {
        ${(0,d.mb)(0)};
    }
`,eN=(0,a.css)`
    display: flex;
    justify-content: space-between;
    margin-bottom: 1rem;
`,ez=e=>(0,a.css)`
    word-break: break-word;
    max-width: 75%;

    @media (min-width: ${e.breakpoints.md}) {
        max-width: 70%;
    }
`,eF=e=>{var t;let r=(0,s.u)(),{isMobile:n}=(0,j.useUserDevice)(),[a,l]=(0,i.useState)(!1),[c,u]=(0,i.useState)(!1),[p,f]=(0,i.useState)(null),m=null==(t=e.offer)?void 0:t.geo_point.coordinates;return(0,o.jsxs)("div",{css:eV,className:e.className,children:[e.hideHeader?null:(0,o.jsxs)("div",{css:eU,children:[(0,o.jsx)(v.Text,{as:"span",variant:"headline_6",children:"Moje miejsca"}),e.disableCollapsible?null:(0,o.jsx)("span",{css:eG,onClick:()=>l(e=>!e),children:a?(0,o.jsx)(ev.ChevronDownIcon,{size:"2"}):(0,o.jsx)(ey.ChevronUpIcon,{size:"2"})})]}),(0,o.jsxs)("div",{css:a&&!e.disableCollapsible?eB:null,children:[(!c||n)&&(0,o.jsx)(eE,{onUserPoiEdit:({id:e,lat:t,lng:r,name:o,tags:i})=>{f({name:o,location:{label:i.address,value:e,coordinates:[t,r]}}),u(!0)},targetCoords:m}),c?(0,o.jsx)("div",{css:eH,children:(0,o.jsx)(eC,{formInitialValues:p,onHideForm:()=>{u(!1),f(null)},targetCoords:m})}):(0,o.jsxs)("div",{css:[ep.flexAbsoluteCenter,ef.pointer],onClick:()=>{u(!0),ei.poiAnalytics.gtm.mapEvent({action:ei.PoiGTMModalAction.CREATE_MY_POI_OPEN})},children:[(0,o.jsx)(eh.PlusIcon,{size:"2",wrapperColor:r.colors.primary,wrapperSize:"2.4"})," ",(0,o.jsx)(v.Text,{variant:"button_small",css:(0,d.ml)(),children:"Dodaj własne miejsce"})]})]})]})},eV=e=>(0,a.css)`
    background-color: #fff;
    width: 100%;
    ${(0,d.mt)(6)};

    @media (min-width: ${e.breakpoints.md}) {
        width: 26.4rem;
        ${(0,eu.elevation)()};
        ${(0,em.borderRadius)(2)};
        ${(0,c.p)(2)};
        ${(0,d.mt)(0)};
    }
`,eU=(0,a.css)`
    ${(0,ep.flex)("center","space-between")};
    user-select: none;
    ${(0,d.mb)(3)};
`,eG=e=>(0,a.css)`
    cursor: pointer;

    @media (max-width: ${e.breakpoints.md}) {
        display: none;
    }
`,eB=(0,a.css)`
    height: 0;
    overflow: hidden;
`,eH=e=>(0,a.css)`
    @media (max-width: ${e.breakpoints.md}) {
        ${(0,c.pb)(4)};
        ${(0,d.mb)(3)};
    }
`,eW=r(73680),eZ=e=>{var t,r,a,C,I,D,$,ee,et,er;let{offer:ei}=e,es=(0,n.useDispatch)(),{isMobile:ea}=(0,j.useUserDevice)(),el=(0,s.u)(),[eu,ep]=(0,i.useState)(!1),{checkedPoiTypes:ef,onEndPoiEditing:em,onStartPoiEditing:ev,setCheckedPoiTypes:ey,poiDistance:eh,setPoiDistance:eg}=(e=>{let t=(0,n.useDispatch)(),{isMobile:r}=(0,j.useUserDevice)(),[o,s]=(0,i.useState)(null!=e?e:[V.PoiType.TRANSPORT]),[a,l]=(0,i.useState)(J.POI_DISTANCE_DEFAULT_VALUE),c=(0,i.useRef)([]),d=(0,i.useRef)([]),u=(0,n.useSelector)(e=>e.maps.userPoi);return{checkedPoiTypes:o,onEndPoiEditing:()=>{r&&(t((0,X.restoreUserPoi)(d.current)),s(c.current),c.current=[],d.current=[])},onStartPoiEditing:()=>{r&&(c.current=o,d.current=u)},setCheckedPoiTypes:s,poiDistance:a,setPoiDistance:l}})(e.initialPoiTypes),eb=t=>{var r;eg(t),null==(r=e.onDistanceChange)||r.call(e,t)},{userPoiMarkers:ex,poisMarkers:ej,poiDirectionsPolylineCoord:eO}=((e,t)=>{let{poiDirectionsPolylineCoord:r}=(0,R.useGooglePoiTravelDirections)(),o=((e,t,r)=>{var o;let s=(0,n.useDispatch)(),{data:a}=(0,N.useGetOfferDetailPoiByTypeQuery)({offerId:e,poiTypes:null==r?void 0:r.checkedPoiTypes},{skip:!(null==r?void 0:r.checkedPoiTypes)||0===r.checkedPoiTypes.length}),{poisFromApi:l,transportPoisFromApi:c}=(0,i.useMemo)(()=>{var e,t,o,i;return{poisFromApi:(null==r||null==(e=r.checkedPoiTypes)?void 0:e.length)&&(null==a||null==(t=a.poi)?void 0:t.pois)||{},transportPoisFromApi:(null==r||null==(o=r.checkedPoiTypes)?void 0:o.length)&&(null==a||null==(i=a.poi)?void 0:i.pois.transport)||{}}},[a,null==r||null==(o=r.checkedPoiTypes)?void 0:o.join(",")]),{educationPois:d,entertainmentPois:u,foodPois:p,healthPois:f,sportPois:m,shopPois:v}=(0,U.usePois)(l,null==r?void 0:r.radiusInMeters),{transportPois:y}=(0,G.useTransportPois)(c,{longitude:t[0],latitude:t[1],radius:(null==r?void 0:r.radiusInMeters)||3e3}),h=(0,F.createGetOsmPoiMarker)((e,t)=>s((0,S.setActivePoi)(e,t)),t),{subwayPoi:g,railwayPoi:b,tramPoi:x,busPoi:j}=(0,G.useTransportPoisStats)(),O=(0,i.useMemo)(()=>{let e=Object.keys(y||{}),t=(null==r?void 0:r.disableInitiallyOpenedPoiId)?void 0:(null==g?void 0:g.id)||(null==b?void 0:b.id)||(null==j?void 0:j.id)||(null==x?void 0:x.id);return y?e.reduce((e,r)=>e.concat(...y[r].map(e=>e.id===t?h(e,V.PoiType.TRANSPORT,z.activeTransportMarkerUrls[r],{initiallyOpened:!0},r):h(e,V.PoiType.TRANSPORT,z.activeTransportMarkerUrls[r],{},r))),[]):[]},[null==r?void 0:r.disableInitiallyOpenedPoiId,null==g?void 0:g.id,null==b?void 0:b.id,null==x?void 0:x.id,null==j?void 0:j.id,y]),P=(0,i.useMemo)(()=>d.map(e=>h(e,V.PoiType.EDUCATION,B)),[d]),w=(0,i.useMemo)(()=>u.map(e=>h(e,V.PoiType.ENTERTAINMENT,Z)),[u]),_=(0,i.useMemo)(()=>p.map(e=>h(e,V.PoiType.FOOD,K)),[p]),T=(0,i.useMemo)(()=>f.map(e=>h(e,V.PoiType.HEALTH,W)),[f]),k=(0,i.useMemo)(()=>m.map(e=>h(e,V.PoiType.SPORT,H)),[m]),C=(0,i.useMemo)(()=>v.map(e=>h(e,V.PoiType.SHOPS,q)),[v]);return(0,i.useMemo)(()=>({[V.PoiType.EDUCATION]:P,[V.PoiType.ENTERTAINMENT]:w,[V.PoiType.FOOD]:_,[V.PoiType.HEALTH]:T,[V.PoiType.SHOPS]:C,[V.PoiType.SPORT]:k,[V.PoiType.TRANSPORT]:O}),[P,w,_,T,C,k,O])})(e.id,e.geo_point.coordinates,t),{userPoiMarkers:s}=(e=>{let t=(0,n.useDispatch)(),r=(0,n.useSelector)(e=>e.maps.userPoi),o=(0,F.createGetOsmPoiMarker)((e,r)=>t((0,S.setActivePoi)(e,r)),null==e?void 0:e.geo_point.coordinates);return{userPoiMarkers:(0,i.useMemo)(()=>r.map(e=>o(e,V.PoiType.USER,Q,{listenToActivePoiDirections:!0})),[r])}})(e);return{userPoiMarkers:s,poiDirectionsPolylineCoord:r,poisMarkers:o}})(e.offer,{disableInitiallyOpenedPoiId:e.disableInitiallyOpenedPoiId,checkedPoiTypes:ef,radiusInMeters:eh?1e3*eh:void 0}),eP=(0,Y.useOsmPoisRoutesGrouped)({longitude:ei.geo_point.coordinates[0],latitude:ei.geo_point.coordinates[1],radius:eh?1e3*eh:3e3}),ew=!!(e.showTransportLines&&ef.includes(V.PoiType.TRANSPORT)),eS=(0,P.useOfferListMapRailTransportElements)({shouldFetch:ew,routes:[eP]}),e_=(0,n.useSelector)(e=>e.maps.travelDirections.activePoi),eT=(0,n.useSelector)(e=>e.maps.travelDirections.activePoiType),ek=(0,n.useSelector)(e=>e.maps.travelDirections.activePoiRoute),eC=(0,_.useOpenStreetMapAlgolyticsTracking)(e.viewType),{polyline:eM,markers:eI}=((e,t)=>{let r=(0,s.u)(),{poiRouteWithStops:a,poiRouteStops:l}=(e=>{let t=(0,n.useSelector)(t=>{var r;return null==(r=t.maps.poi.poiRoute)?void 0:r[e.poiId]})||null,r=(0,n.useDispatch)();(0,i.useEffect)(()=>{e.skipFetching||r((0,E.fetchPublicTransportRoute)(e))},[e.poiId]);let o=(0,i.useMemo)(()=>(null==t?void 0:t.stops)||[],[t]),s=(0,i.useMemo)(()=>{var e;return(null==t||null==(e=t.geometry)?void 0:e.coordinates)||[]},[t]);return{poiRouteWithStops:t,poiRouteStops:o,poiRouteGeometryCoordinates:s}})({poiId:(null==t?void 0:t.id)||0,skipFetching:!(null==t?void 0:t.id)});return(0,i.useMemo)(()=>{let t=l.filter(e=>Number.isFinite(e.coordinates[0])&&Number.isFinite(e.coordinates[1])),i=((e,t)=>{if(!e)return null;let r=null,o=Number.MAX_SAFE_INTEGER;return t.forEach(t=>{let i=(0,T.countDistance)((0,k.convertToLatLngLiteralOfPoland)(t.coordinates),(0,k.convertToLatLngLiteralOfPoland)(e));i<o&&(o=i,r=t)}),r})(e,t);return{polyline:a?(0,L.getMapTransportPolyline)(function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},a),r):null,markers:a?t.filter(t=>(function(e,t){let r=(0,k.convertToLatLngLiteralOfPoland)(e),o=(0,k.convertToLatLngLiteralOfPoland)(t);return(0,T.countDistance)(r,o)})(e,t.coordinates)>3e3).map(e=>(0,A.getMapPassiveTransportStopMarker)(e,a.type,i,()=>(0,o.jsx)(M,{poiRoute:a}))):[],stops:t,nearestStop:i}},[null==t?void 0:t.id,null==a?void 0:a.id])})(ei.geo_point.coordinates,ek),eD=(0,i.useMemo)(()=>{var t,r;return{center:(0,g.convertToCountryLatLngLiteral)((null==(t=e.offer)?void 0:t.geo_point.coordinates)||[],null==(r=e.offer)?void 0:r.region.country),radius:500}},[null==(t=e.offer)?void 0:t.geo_point.coordinates[0],null==(r=e.offer)?void 0:r.geo_point.coordinates[1]]),e$=(0,i.useMemo)(()=>[...eI,...(()=>{let{offer:t}=e;return t?[{id:t.id,coords:(0,g.convertToCountryLatLngLiteral)(t.geo_point.coordinates,t.region.country),zIndexOffset:2,icon:{url:eW,sizes:[30,38]},popup:()=>(0,o.jsx)(en,{offer:t}),popupShowCloseButton:!0,onClick:()=>{es((0,S.setActivePoi)(null,null)),es((0,S.setActivePoiDirections)(null))}}]:[]})(),...ef.reduce((e,t)=>e.concat(...ej[t]||[]),[]),...(e.customPoiMarkers||[]).filter(e=>e.poiType&&ef.includes(e.poiType)),...ex,...e.customMarkers||[],...eS&&eS.markers&&ew?eS.markers:[]],[eI,null==(a=e.offer)?void 0:a.id,null==(C=e.offer)?void 0:C.geo_point.coordinates[0],null==(I=e.offer)?void 0:I.geo_point.coordinates[1],ef,ex,e.customMarkers,ej,ew,eS.markers]),eA=(0,i.useDeferredValue)(e$),eL=(0,i.useMemo)(()=>[{id:"default-polygon",positions:(e.offer?(0,b.convertToArrayOfLatLngLiterals)(e.offer.geo_area.coordinates.coordinates,{reversedValues:!0}):e.polygon?(0,b.convertToArrayOfLatLngLiterals)(e.polygon.coordinates[0],{reversedValues:!0}):void 0)||[],pathOptions:{fillColor:"#FFCDA5",color:"#23232D",fillOpacity:.8,weight:2}},...e.detailPolygons?e.detailPolygons.map(e=>{var t,r,i;return{id:JSON.stringify(e.coords),positions:(0,b.convertToArrayOfLatLngLiterals)(e.coords,{reversedValues:!0}),height:e.height||1,popup:(null==e||null==(t=e.infoWindow)?void 0:t.content)?()=>{var t;return(0,o.jsx)(v.Text,{variant:"headline_4",css:[(0,c.ph)()],children:`${null==e||null==(t=e.infoWindow)?void 0:t.content}`})}:void 0,pathOptions:{fillColor:null==(r=e.options)?void 0:r.fillColor,color:null==(i=e.options)?void 0:i.strokeColor}}}):[]],[null==(D=e.offer)?void 0:D.id,null==($=e.offer)?void 0:$.geo_point.coordinates[0],null==(ee=e.offer)?void 0:ee.geo_point.coordinates[1],e.polygon,e.detailPolygons]),eE=(0,i.useMemo)(()=>[{id:"travel",positions:eO,pathOptions:{color:el.colors.danger,weight:5}},...eM?[eM]:[],...eS&&eS.polylines&&ew?eS.polylines:[]],[eO,eM,ew,eS.polylines]),eR=(0,i.useMemo)(()=>e.drawPoiDistance?[{center:(0,g.convertToCountryLatLngLiteral)(ei.geo_point.coordinates,ei.region.country),radius:1e3*eh,pathOptions:{color:"#EBFF00",opacity:.3}}]:[],[e.drawPoiDistance,ei.geo_point.coordinates,ei.region.country,eh]),eN=(0,i.useCallback)(t=>{var r;return!0===ea&&t.id!==(null==(r=e.offer)?void 0:r.id)},[ea,null==(et=e.offer)?void 0:et.id]),ez=(0,i.useMemo)(()=>{var t,r,i,n,s,a,l,c;return(0,o.jsx)(o.Fragment,{children:(0,o.jsx)(x.LazyOpenStreetMap,(l=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({scrollWheelZoom:null==(a=null==(t=e.mapConfig)?void 0:t.scrollWheelZoom)||a,fitBounds:null==(r=e.mapConfig)?void 0:r.fitBounds},eC),c=c={minFitBounds:eD,polygons:eL,markers:eA,polylines:eE,markerShowPopupOnHover:!1,markerDisablePopup:eN,maxZoom:(null==(i=e.mapConfig)?void 0:i.maxZoom)||16,clusterMarkers:e.clusterMarkers,tileUrl:(null==(n=e.offer)?void 0:n.region.country)===w.Country.SPAIN?O.osmPublicTileUrl:null,fitBoundsDefaultZoom:null==(s=e.mapConfig)?void 0:s.fitBoundsDefaultZoom,circles:eR,onMarkerInvalidCoords:e=>{let t="Invalid marker coords in OpenStreetMapsWithPoi";(0,y.notifyBugsnagClient)(Error(t),t,JSON.stringify(e))},className:e.className,onFullscreenClick:e.onFullscreenClick},Object.getOwnPropertyDescriptors?Object.defineProperties(l,Object.getOwnPropertyDescriptors(c)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(c)).forEach(function(e){Object.defineProperty(l,e,Object.getOwnPropertyDescriptor(c,e))}),l))})},[null==(er=e.mapConfig)?void 0:er.scrollWheelZoom,eC.onMapMove,eC.onMapInit,eL,eE,eA]);return(0,h.useIsMounted)()&&e.offer?(0,o.jsxs)("div",{css:[u.w100,p.h100],children:[e.disablePoiSwitch?null:(0,o.jsx)(f.FiltersIcon,{wrapperSize:"4",size:"2.4",wrapperColor:el.colors.primary,onClick:()=>{ev(),ep(!0)},css:[eK,eQ(e.mobilePoiModalTriggerPosition)]}),e.children?e.children({setCheckedPoiTypes:ey,checkedPoiTypes:ef,poiDistance:eh,setPoiDistance:eb,map:ez}):(0,o.jsxs)(o.Fragment,{children:[e.disablePoiSwitch?null:(0,o.jsxs)("div",{css:eq,children:[(0,o.jsx)(ec.PoiSwitcher,{onChange:ey,checkedPoiTypes:ef,distanceValue:eh,onDistanceChange:eb}),(0,o.jsx)("div",{css:[(0,d.mt)(2)],children:(0,o.jsx)(eF,{offer:e.offer})})]}),ez]}),e.disablePoiSwitch?null:(0,o.jsx)(eo,{modalState:eu,onModalClose:e=>{e&&em(),ep(!1)},children:(0,o.jsxs)(i.Fragment,{children:[(0,o.jsx)(ec.PoiSwitcher,{onChange:ey,checkedPoiTypes:ef,distanceValue:eh,onDistanceChange:eb}),(0,o.jsx)(eF,{offer:e.offer})]})}),(0,o.jsx)("div",{css:eY,id:"poiTravelModeInfoWindowMobile",children:ea&&e_&&eT?(0,o.jsx)(ed.PoiTravelModeInfoWindow,{calcTravelDataOnOpen:!0,poi:e_,poiType:eT,targetCoords:e.offer.geo_point.coordinates}):null}),e.mapBottomSlot?(0,o.jsx)("div",{css:eX,children:e.mapBottomSlot}):null]}):(0,o.jsx)(l.CenterBox,{children:(0,o.jsx)(m.Loader,{size:"lg"})})},eq=e=>(0,a.css)`
    position: absolute;
    top: 2rem;
    left: 2.5rem;
    z-index: ${10};

    @media (max-width: ${e.breakpoints.md}) {
        display: none;
    }
`,eK=e=>(0,a.css)`
    position: absolute;
    top: 1.6rem;
    right: 1.6rem;
    z-index: ${10};
    cursor: pointer;

    @media (min-width: ${e.breakpoints.md}) {
        display: none;
    }
`,eQ=e=>(0,a.css)`
    ${"center"===e?(0,a.css)`
              right: 0;
              left: 0;
              ${(0,d.mh)("auto")};
          `:""};
`,eY=e=>(0,a.css)`
    position: fixed;
    bottom: 1.6rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10;
    width: calc(100% - 3.2rem);

    @media (min-width: ${e.breakpoints.md}) {
        display: none;
    }
`,eX=(0,a.css)`
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
`},86557:function(e,t,r){r.r(t),r.d(t,{POI_DISTANCE_DEFAULT_VALUE:()=>i,POI_DISTANCE_VALUES:()=>o,poiDistanceSelectOptions:()=>n});let o=[1,3,5],i=3,n=o.map(e=>({value:e,label:`+${e} km`}))},34978:function(e,t,r){r.r(t),r.d(t,{useGooglePoiTravelDirections:()=>d});var o=r(2784),i=r(95397),n=r(70252),s=r(73916),a=r(26082);function l(e,t,r,o,i,n,s){try{var a=e[n](s),l=a.value}catch(e){r(e);return}a.done?t(l):Promise.resolve(l).then(o,i)}function c(e){return function(){var t=this,r=arguments;return new Promise(function(o,i){var n=e.apply(t,r);function s(e){l(n,o,i,s,a,"next",e)}function a(e){l(n,o,i,s,a,"throw",e)}s(void 0)})}}let d=()=>{let e=(0,i.useDispatch)(),t=(0,i.useSelector)(e=>e.maps.travelDirections.activePoiDirections),r=(0,i.useSelector)(e=>e.maps.travelDirections.poisDirections),l=(0,o.useCallback)((t,r,o,i)=>c(function*(){if(yield(0,n.loadGoogleMapsApi)(["routes"]),window&&window.google){let n,l=new window.google.maps.DirectionsService,[d,u]=o,{lng:p,lat:f}=t;return n={destination:new window.google.maps.LatLng(f,p),origin:new window.google.maps.LatLng(u,d),travelMode:i},c(function*(){return new Promise(o=>{l.route(n,(l,c)=>{var d,u,p;if(c===(null==(d=window.google.maps)?void 0:d.DirectionsStatus.OK)&&l){let c=l.routes[0],d=(null==(u=c.legs[0].duration)?void 0:u.value)||0,f=(null==(p=c.legs[0].distance)?void 0:p.value)||0,m=[];return c.legs&&(m=(0,a.getPolylineCoords)(c.legs[0])),e((0,s.setPoisDirections)({id:t.id,travelMode:i,data:{duration:d,distance:f,polylineCoords:m}})),e((0,s.setActivePoiDirections)({id:t.id,travelMode:i,poiType:r})),o({type:n.travelMode,duration:d,distance:f})}return o(null)})})})()}return Promise.reject("Google Maps API not defined")})(),[]);return{poiDirectionsPolylineCoord:(0,o.useMemo)(()=>t?r[t.id][t.travelMode].polylineCoords:[],[t,r]),getPoiDirections:l}}},6982:function(e,t,r){r.r(t),r.d(t,{useMapNearbyOffersPois:()=>J});var o=r(52903),i=r(2784),n=r(93445),s=r(70278),a=r(33374),l=r(70622),c=r(75264),d=r(28165),u=r(35648),p=r(75109),f=r(38633),m=r(6291),v=r(90751),y=r(57144),h=r(35554),g=r(86330),b=r(21493),x=r(40760),j=r(25694),O=r(29043),P=r(48624),w=r(69155),S=r(67823);let _=e=>{var t,r,n;let s=(0,c.u)(),{name:a,stats:l,region:d,vendor:u,type:p}=e.offerDetails,f=(0,P.getCurrency)({country:d.country}),_=(null==l?void 0:l.properties_count_for_sale)||0,R="construction_date_range"in e.offerDetails&&(null==(r=e.offerDetails)||null==(t=r.construction_date_range)?void 0:t.upper),N="main_image"in e.offerDetails?null==(n=e.offerDetails.main_image)?void 0:n.m_img_375x211:void 0,z=(0,w.useOfferLink)(e.offerDetails),F="horizontal"===e.type,V=l&&"ranges_price_min"in l&&l.ranges_price_min?(0,x.priceFormat)(l.ranges_price_min,{unit:f}):l&&"ranges_price_m2_min"in l&&l.ranges_price_m2_min?(0,x.priceM2Format)(l.ranges_price_m2_min,{unit:f}):null;return(0,i.useEffect)(()=>{O.poiAnalytics.gtm.mapEvent({action:O.PoiGTMModalAction.MAP_INVESTMENT_MARKER_CLICK,label:"investment"})},[]),(0,o.jsxs)("div",{css:F?k:T,onClick:()=>{O.poiAnalytics.gtm.mapEvent({action:O.PoiGTMModalAction.MAP_INVESTMENT_SELECT,label:"investment"}),window.open(z,"_blank")},children:[N?(0,o.jsx)(h.Image,{imageStyle:{objectFit:"cover"},width:F?"135px":"100%",height:F?"96px":"100px",src:N,css:F?L:A,alt:`${a} - zdj\u{119}cie`}):null,(0,o.jsxs)("div",{css:F?M:C,children:[F?(0,o.jsx)("div",{css:E,onClick:t=>{var r;t.stopPropagation(),null==(r=e.onCloseClick)||r.call(e)},children:(0,o.jsx)(m.CloseIcon,{size:"1.6"})}):null,(0,o.jsx)(g.Text,{as:"div",variant:"info_txt_1",children:a}),(0,o.jsx)(g.Text,{as:"div",variant:"info_txt_3",color:s.colors.gray[600],children:u.name}),V?(0,o.jsx)(g.Text,{as:"div",variant:"info_txt_2",css:I,children:(0,o.jsxs)(b.Highlight,{children:["od ",V]})}):null,(0,o.jsxs)("div",{css:D,children:[_>0?(0,o.jsxs)("div",{css:$,children:[(0,o.jsx)(v.PropertyPlanIcon,{size:"1.2"}),(0,o.jsxs)(g.Text,{as:"span",variant:"info_txt_3",children:[_," ",(0,S.getOfferTypePluralize)(_,p)]})]}):null,R?(0,o.jsxs)("div",{css:$,children:[(0,o.jsx)(y.CalendarCheckIcon,{size:"1.2"}),(0,o.jsx)(g.Text,{as:"span",variant:"info_txt_3",children:(0,j.formatFutureDate)(R,j.dateTimeFormat.quarterLong)})]}):null]})]})]})},T=(0,d.css)`
    min-width: 20rem;
    cursor: pointer;
`,k=(0,d.css)`
    display: flex;
    flex-direction: row;
    width: 100%;
    cursor: pointer;
`,C=(0,d.css)`
    position: relative;
    ${(0,u.p)(1)};
`,M=(0,d.css)`
    position: relative;
    ${(0,u.p)(1)};
    width: 100%;
`,I=(0,d.css)`
    ${(0,p.mt)(.5)};
`,D=(0,d.css)`
    ${(0,u.pt)(1)};
    display: flex;
    justify-content: space-between;
`,$=(0,d.css)`
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: ${(0,f.calculateRemSize)(.5)};
`,A=(0,d.css)`
    width: 100%;
`,L=(0,d.css)`
    flex: 0 0 135px;
`,E=(0,d.css)`
    ${(0,u.p)(1)};
    display: flex;
    justify-content: center;
    align-items: center;
    position: absolute;
    top: 0;
    right: 0;
`;var R=r(88838),N=r(78982);function z(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}var F=r(16709),V=r.n(F);let U=e=>(0,o.jsx)(g.Text,{as:"div",variant:"info_txt_1",className:V()("QHQgploih_ALDkyq"),children:e.text});var G=r(75288),B=r(55155);let H=(0,i.forwardRef)((e,t)=>(0,o.jsx)("div",{ref:t,css:W,children:e.children})),W=(0,d.css)`
    ${(0,p.m)(1.5,"auto")};
    display: flex;
    justify-content: center;
    width: 100%;
    max-width: 34rem;
    background: #fff;
    ${(0,G.borderRadius)(2)};
    overflow: hidden;
    ${(0,B.elevation)(4)};
`;var Z=r(11646),q=r(95397),K=r(46482),Q=r(19985),Y=r(73916);let X=r.p+"f2392dcc95b37338.svg",J=e=>{let{baseOffer:t,showPropertyNumberOnMarker:r}=e,[c,d]=(0,i.useState)(null),u=(0,i.useRef)(null),{isMobile:p}=(0,s.useUserDevice)(),f=(0,n.usePrevious)(c,c),m=(0,i.useRef)(null);(0,a.useClickOutside)(u,()=>{m.current=setTimeout(()=>{f===c&&d(null)},300)});let v={offer:{id:t.id,type:t.type},distance:e.distance};"stats"in t&&t.stats&&(v.offer.areaMin=t.stats.ranges_area_min,v.offer.areaMax=t.stats.ranges_area_max),"stats"in t&&t.stats&&t.stats.rooms&&t.stats.rooms.length&&(v.offer.roomsMin=Math.min(...t.stats.rooms),v.offer.roomsMax=Math.max(...t.stats.rooms));let{data:y}=(0,l.useGetOfferListQuery)(function(e){var t,r;let{page:o=1,offer:{id:i,type:n}}=e,s=z({},e.offer.areaMin?{area_0:Math.floor(Math.min(.9*e.offer.areaMin,e.offer.areaMin-5))}:{},e.offer.areaMax?{area_1:Math.ceil(Math.max(1.1*e.offer.areaMax,e.offer.areaMax+5))}:{},e.offer.roomsMin?{rooms_0:e.offer.roomsMin}:{},e.offer.roomsMax?{rooms_1:e.offer.roomsMax}:{});return t=z({},R.detailOfferListConstraints,s),r=r={page:o,page_size:50,type:n,near_by_offer:i,exclude_offer:i,distance:e.distance||N.DEFAULT_DISTANCE_NEARBY_OFFERS},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t}(v)),h=(e=>{let{offers:t,iconUrl:r,iconSizes:n,renderer:s,onClick:a}=e,l=(0,q.useDispatch)(),c=e=>({id:e.id,coords:(0,K.convertToCountryLatLngLiteral)(e.geo_point.coordinates,e.region.country),popup:()=>(0,o.jsx)(_,{type:"vertical",offerDetails:e}),icon:{url:r||X,sizes:n||[24,24],renderer:s?()=>null==s?void 0:s(e):void 0},poiType:Q.PoiType.OFFERS,onClick:()=>{null==a||a(e),l((0,Y.setActivePoi)(null,null)),l((0,Y.setActivePoiDirections)(null))}});return(0,i.useMemo)(()=>t?t.map(c):[],[t])})({offers:null==y?void 0:y.results,renderer:r?e=>{var t;return(0,o.jsx)(U,{text:`${(null==(t=e.stats)?void 0:t.properties_count_for_sale)||""}`})}:void 0,onClick:e=>{p&&(m.current&&clearTimeout(m.current),d(e))}});return{offerAdditionalPois:h,defaultPoiTypes:[Z.PoiType.TRANSPORT,Z.PoiType.OFFERS],mapBottomSlot:c?(0,o.jsx)(H,{ref:u,children:(0,o.jsx)(_,{type:"horizontal",offerDetails:c,onCloseClick:()=>d(null)})}):null}}},29043:function(e,t,r){r.r(t),r.d(t,{PoiGTMModalAction:()=>l,poiAnalytics:()=>d});var o,i=r(34213),n=r(65006),s=r(52098);function a(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}var l=((o={}).CREATE_MY_POI_OPEN="create_my_poi_open",o.CREATE_MY_POI_SUBMIT="create_my_poi_submit",o.DELETE_MY_POI="delete_my_poi",o.IMPORTANT_PLACES_OFF="important_places_off",o.IMPORTANT_PLACES_ON="important_places_on",o.MAP_POI_CLICK="map_poi_click",o.MAP_INVESTMENT_MARKER_CLICK="click",o.MAP_INVESTMENT_SELECT="select",o.MAP_FIRST_INTERACTION="interaction",o.MAP_POI_CALCULATE="map_poi_calculate",o.MY_POI_CALCULATE="my_poi_calculate",o);let c=e=>(0,i.delayHit)(t=>(0,i.hitAlgolytics)(e,a({},t,(0,n.getTrackedSiteData)())),500),d={algolytics:{addMyPoi:(e,t,r,o)=>{let i={address:t.tags.address,event_type:"add_my_poi",geo_point:[t.lat,t.lng],offer_id:r?Number(r):null,poi_name:t.name,property_id:o?Number(o):null,view_type:e};c("map_events_my_poi")(i)},poiClick:(e,t,r,o,i)=>{let n={category_id:t,event_type:"poi_click",geo_point:[r.lat,r.lng],offer_id:o?Number(o):null,poi_id:r.id,poi_name:r.name,property_id:i?Number(i):null,view_type:e};c("map_events_poi_click")(n)},meansOfTransportClick:(e,t,r,o,i,n,s)=>{let a={category_id:t,time:i,event_type:"means_of_transport",means_of_transport:o,offer_id:n?Number(n):null,poi_id:r.id,poi_name:r.name,property_id:s?Number(s):null,view_type:e};c("map_events_means_of_transport")(a)},showPoi:(e,t,r,o,i)=>{let n={category_id:r,checked:t,event_type:"show_poi",offer_id:o?Number(o):null,property_id:i?Number(i):null,view_type:e};c("map_events_show_poi")(n)}},gtm:{mapEvent:e=>{let t=a({event:"map",label:""},e);(0,s.hitGoogleTagManager)(t)}}}},29313:function(e,t,r){r.r(t),r.d(t,{hitGtmBusRouteClick:()=>i});var o=r(52098);let i=()=>{(0,o.hitGoogleTagManager)({event:"map_poi_bus_route"})}},67108:function(e,t,r){r.r(t),r.d(t,{createGetOsmPoiMarker:()=>c});var o=r(52903);r(2784);var i=r(28165),n=r(91114),s=r(11646);function a(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}let l={calcTravelDataOnOpen:!0},c=(e,t)=>(r,i,c,u,p)=>{var f,m;let v=a((f=a({},l),m=m={poi:r,poiType:i,targetCoords:t},Object.getOwnPropertyDescriptors?Object.defineProperties(f,Object.getOwnPropertyDescriptors(m)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(m)).forEach(function(e){Object.defineProperty(f,e,Object.getOwnPropertyDescriptor(m,e))}),f),u);return{id:r.id,coords:{lng:r.lng,lat:r.lat},icon:{url:c,sizes:[32,32]},onClick:()=>{e(r,i)},onInit:()=>{(null==u?void 0:u.initiallyOpened)&&e(r,i)},popup:e=>(0,o.jsx)("div",{css:d,children:(0,o.jsx)(n.PoiTravelModeInfoWindow,a({onClose:()=>{var t;null==e||null==(t=e.current)||t.closePopup()}},v))}),manualActive:()=>{null==e||e(r,i)},skipInFitBounds:r.distance>700,isPopupInitiallyOpened:i===s.PoiType.USER||!!(null==u?void 0:u.initiallyOpened),poiType:i,poiSubType:p}},d=(0,i.css)`
    animation: popupAppear 0.3s ease-out;
    min-width: 24rem;

    @keyframes popupAppear {
        0% {
            opacity: 0;
            transform: translateY(5px);
        }
        60% {
            opacity: 0;
            transform: translateY(5px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
`},87630:function(e,t,r){r.r(t),r.d(t,{getHasCountryPois:()=>i});var o=r(76755);let i=e=>[o.Country.POLAND].includes(e)},26082:function(e,t,r){r.r(t),r.d(t,{getPolylineCoords:()=>o});let o=e=>e.steps.reduce((e,t)=>(t.path.forEach(t=>{e.push({lat:t.lat(),lng:t.lng()})}),e),[])},85866:function(e,t,r){r.r(t),r.d(t,{isValidLocationObject:()=>o});let o=e=>"object"==typeof e&&Object.prototype.hasOwnProperty.call(e,"value")&&Object.prototype.hasOwnProperty.call(e,"label")},70622:function(e,t,r){r.r(t),r.d(t,{getOfferList:()=>a,useGetOfferListQuery:()=>l,useGetPrivilegedOfferListQuery:()=>c});var o=r(67734),i=r(94362),n=r(20113);let s=i.apiV2ListLink.offer.list(i.Scenario.OFFER_LIST),a=n.rpApi.injectEndpoints({endpoints:e=>({getOfferList:e.query({query:e=>({url:s,params:e})}),getPrivilegedOfferList:e.query({query:e=>({url:s,params:e}),transformResponse:(e,t,r)=>{let i=r.include_offer.map(t=>e.results.find(e=>e.id===t)),n=(0,o.compact)(i);return{results:n,page:1,count:n.length,next:null,previous:null,page_size:n.length}}})})}),{useGetOfferListQuery:l,useGetPrivilegedOfferListQuery:c}=a},26412:function(e,t,r){r.r(t),r.d(t,{OfferModalLayout:()=>s});var o=r(28165),i=r(7184),n=r(95420);let s=i.default.div`
    ${({mobileImageOpened:e,theme:t})=>(0,o.css)`
        display: flex;
        flex-direction: column;
        height: 100%;
        position: relative;
        overflow: ${e?"hidden":"scroll"};
        background: ${t.colors.gray[100]};

        ${(0,n.onDesktop)((0,o.css)`
            overflow: visible;
            background: transparent;
        `)}
    `}
`},37250:function(e,t,r){r.r(t),r.d(t,{OfferModal:()=>ry});var o=r(52903),i=r(2784),n=r(28165),s=r(7184),a=r(83397),l=r(95420),c=r(94507),d=r(39754);let u=`
    height: 100%;
`;var p=r(75109);let f=e=>`
    width: ${e}%;
    flex-basis: ${e}%;
`;f(25),f(33),f(50),f(66),f(75);let m=f(100);var v=r(35554),y=r(37867),h=r(4349),g=r(70278),b=r(7267),x=r(51267);let j=e=>{var t,r;let o=(0,b.useLocation)(),n=(0,b.useHistory)(),s=(0,x.useRoutedModalState)(e.routeParam,e.value),a=(0,i.useRef)({paramsModalState:e.idOpenStoreState,routedModalState:s.modalState}),l=e=>{a.current={paramsModalState:e,routedModalState:e}};return(0,i.useEffect)(()=>{if(j.hasBeenMounted)return;let t=new URLSearchParams(o.search);e.routeParam&&e.removeRouteParamFromUrlOnFirstMount&&t.has(e.routeParam)&&(t.delete(e.routeParam),n.replace({search:t.toString()})),j.hasBeenMounted=!0},[]),(0,i.useEffect)(()=>{if(e.idOpenStoreState!==a.current.paramsModalState)e.idOpenStoreState&&e.disableOpenAction||(e.idOpenStoreState?(s.openModal(),l(!0)):(s.closeModal(!0),l(!1)));else if(s.modalState!==a.current.routedModalState){if(s.modalState&&e.disableOpenAction)return;e.setModalState(s.modalState),l(s.modalState)}},[s.modalState,e.idOpenStoreState]),t=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},s),r=r={isOpen:!e.disableOpenAction&&s.modalState,modalState:void 0},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t};j.hasBeenMounted=!1;var O=r(38633),P=r(75288),w=r(35648),S=r(76396),_=r(81130),T=r(86330);let k=r(64164),C=()=>{let[e,t]=(0,i.useState)(!1);return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)("div",{css:I,children:(0,o.jsx)(v.Image,{src:k,alt:"",width:"88",height:"23"})}),(0,o.jsxs)("div",{css:D,children:[e&&(0,o.jsxs)(T.Text,{variant:"info_txt_3",css:$,children:[(0,o.jsx)(M,{url:"https://www.mapbox.com/about/maps/",css:A,children:"\xa9 Mapbox"}),(0,o.jsx)(M,{url:"https://www.openstreetmap.org/about/",css:A,children:"\xa9 OpenStreetMap"}),(0,o.jsx)(M,{url:"https://apps.mapbox.com/feedback/",css:A,children:"Improve this map"})]}),(0,o.jsx)("div",{css:[L,e&&E],onClick:()=>{t(e=>!e)},children:(0,o.jsx)(_.InfoIcon,{size:"1.6"})})]})]})},M=e=>(0,o.jsx)("div",{onClick:()=>{window.open(e.url,"_blank")},className:e.className,children:e.children}),I=(0,n.css)`
    position: absolute;
    left: ${(0,O.calculateRemSize)(1.5)};
    bottom: ${(0,O.calculateRemSize)(1.5)};
    display: inline-flex;
`,D=(0,n.css)`
    position: absolute;
    right: ${(0,O.calculateRemSize)(1.5)};
    bottom: ${(0,O.calculateRemSize)(1.5)};
    display: inline-flex;
    align-items: center;
    background-color: #fff;
    ${(0,P.borderRadius)(2)};
    height: ${(0,O.calculateRemSize)(3)};
`,$=(0,n.css)`
    ${(0,w.pl)(1)};
`,A=e=>(0,n.css)`
    display: inline-flex;
    cursor: pointer;
    ${(0,w.pr)(.5)};

    &:hover {
        color: ${e.colors.highlight};
    }
`,L=(0,n.css)`
    height: ${(0,O.calculateRemSize)(3)};
    width: ${(0,O.calculateRemSize)(3)};
    ${S.flexAbsoluteCenter};
    cursor: pointer;
    user-select: none;
`,E=e=>(0,n.css)`
    background-color: ${e.colors.gray[200]};
    ${(0,P.borderRadius)(2)};
`;var R=r(68786),N=r(8939),z=r(38557),F=r(26412),V=r(75264),U=r(21595),G=r(89143),B=r(66770),H=r(49111),W=r(77605),Z=r(25598),q=r(93148),K=r(30583),Q=r(14273),Y=r(38101),X=r(24252),J=r(68025),ee=r(95397),et=r(71128),er=r(90751),eo=r(89438),ei=r(62749),en=r(64840),es=r(33814),ea=r(64363);let el=e=>{let t=(0,V.u)(),{isMobile:r}=(0,g.useUserDevice)(),n=(0,ee.useDispatch)(),s=(0,R.useAppSelector)(t=>t.offerModals[e.modalName].type),{modalName:a,openFilters:l,openSort:c}=e,d=(0,R.useAppSelector)(e=>e.offerModals[a].filters),u=()=>{if(s===es.PropertyListType.TABLE){(0,ea.hitPropertyListViewChange)("rzuty"),n((0,N.setOfferModalType)({modalName:a,type:es.PropertyListType.TILES}));return}(0,ea.hitPropertyListViewChange)("lista"),n((0,N.setOfferModalType)({modalName:a,type:es.PropertyListType.TABLE}))},p=(0,i.useMemo)(()=>{var e,t,r,o;if(!d)return 0;let i=e=>void 0!==e&&(""!==e.lower||""!==e.upper),n=(null!=(r=null==(e=d.floor_choices)?void 0:e.length)?r:0)>0||(null!=(o=null==(t=d.house_storeys)?void 0:t.length)?o:0)>0;return Number(i(d.price))+Number(i(d.rooms))+Number(i(d.area))+Number(n)},[d]);return(0,o.jsxs)("div",{css:ec,children:[(0,o.jsxs)("div",{css:ed,children:[(0,o.jsxs)(eu,{isActive:"tiles"===s,onClick:u,children:[(0,o.jsx)(er.PropertyPlanIcon,{size:"2.4",wrapperSize:"2.4",wrapperColor:"transparent"}),(0,o.jsx)(T.Text,{color:t.colors.secondary,variant:"button_medium",children:"Rzuty"})]}),(0,o.jsxs)(eu,{isActive:"table"===s,onClick:u,children:[(0,o.jsx)(eo.HorizontalListIcon,{size:"2.4",wrapperSize:"2.4",wrapperColor:"transparent"}),(0,o.jsx)(T.Text,{color:t.colors.secondary,variant:"button_medium",children:"Lista"})]})]}),r&&(0,o.jsxs)("div",{css:ep,children:[(0,o.jsx)(eu,{isActive:!0,onClick:l,children:(0,o.jsxs)("span",{css:ef,children:[(0,o.jsx)(ei.FiltersIcon,{size:"2.4",wrapperSize:"2.4",wrapperColor:"transparent",fill:t.colors.secondary}),p>0&&(0,o.jsx)(et.Badge,{variant:"label_danger",css:em,children:p})]})}),(0,o.jsx)(eu,{isActive:!0,onClick:c,children:(0,o.jsx)(en.SortIcon,{size:"2.4",wrapperSize:"2.4",wrapperColor:"transparent",fill:t.colors.secondary})})]})]})},ec=(0,n.css)`
    display: flex;
    justify-content: space-between;
    flex: 1 1 auto;
    ${(0,d.pv)(2)};

    ${(0,l.onDesktop)((0,n.css)`
        ${(0,d.pv)()};
        column-gap: ${(0,c.calculateRemSize)(2)};
    `)}
`,ed=(0,n.css)`
    ${(0,a.flex)("center")};
    column-gap: ${(0,c.calculateRemSize)(4)};
    ${(0,l.onDesktop)((0,n.css)`
        flex: 2 1 auto;
        justify-content: flex-end;
    `)}
`,eu=s.default.button`
    ${(0,a.flex)("center")};
    column-gap: ${(0,c.calculateRemSize)(1)};
    ${e=>!e.isActive&&(0,n.css)`
            opacity: 0.5;
        `}
`,ep=(0,n.css)`
    ${(0,a.flex)("center")};
    column-gap: ${(0,c.calculateRemSize)(3)};
`,ef=(0,n.css)`
    position: relative;
    display: inline-flex;
`,em=(0,n.css)`
    position: absolute;
    top: -${(0,c.calculateRemSize)(.5)};
    right: -${(0,c.calculateRemSize)(.5)};
    padding: 0.25rem 0.5rem;
    min-height: ${(0,c.calculateRemSize)(2)};
    font-size: ${(0,c.calculateRemSize)(2)};
    line-height: 1;
`;var ev=r(44005),ey=r(40296);let eh=e=>{let{offers:t,page:r,pageSize:o,modalName:i}=e,n=(0,R.useAppSelector)(e=>e.offerModals[i].offerId),s=(0,R.useAppSelector)(e=>e.offerModals[i].offer),a=r>1?(r-1)*o:0,l=t.map((e,t)=>({id:e.id,position:a+t,data:e})),c=l.findIndex(e=>e.id===n)+a,d=s?{id:s.id,position:c,data:s}:l.find(e=>e.id===n);return d||((0,ev.notifyBugsnag)({message:`Offer ${n} is not available in query`,groupingHash:"offer-not-available-in-query"},`Offer ${n} is not available in query`,{offer:s,offersList:t}),(0,ey.addNotification)({notification:{content:`Przepraszamy, wyst\u{105}pi\u{142} b\u{142}\u{105}d podczas \u{142}adowania szczeg\xf3\u{142}\xf3w oferty.`,type:"failure"}}),(0,N.hideOfferModal)({modalName:i})),{selectedOffer:d,offerId:n,offer:s,offersWithPosition:l,offersStartingPosition:a}},eg=e=>{var t;let{modalName:r,offers:n,paginationQuery:{page:s,pageSize:l},isExpanded:c,toggleExpand:d,onHeightUpdate:u,handleFiltersModalVisibility:p,handleSortModalVisibility:f}=e,{isMobile:m}=(0,g.useUserDevice)(),y=(0,Q.useResponsiveLinkTarget)(),b=(0,V.u)(),x=(0,i.useRef)(null),{selectedOffer:j}=eh({offers:n,page:s,pageSize:l,modalName:r});if(!j)return null;let O=j.data,P=(t=O)?(0,X.createOfferLink)(t):"";return(0,i.useEffect)(()=>{let e=null;return"ResizeObserver"in window&&(e=new ResizeObserver(e=>{if(u&&e[0]){var t,r;u((null==(r=e[0].borderBoxSize)||null==(t=r[0])?void 0:t.blockSize)||e[0].contentRect.height+e[0].contentRect.top)}})),x.current&&(null==e||e.observe(x.current)),()=>{x.current&&(null==e||e.unobserve(x.current))}},[]),(0,o.jsxs)(h.SystemModal.Header,{css:eO,as:"div",ref:x,children:[(0,o.jsxs)("div",{css:eP,children:[O.vendor.logo&&(0,o.jsx)(v.Image,{css:eS,width:"120px",height:"90px",alt:`${O.vendor.name} logo`,src:O.vendor.logo.v_log_120x90}),(0,o.jsxs)("div",{css:B.w100,children:[(0,o.jsx)(T.Text,{as:"h2",variant:"headline_3",css:eC,children:(0,o.jsx)("a",{href:P,target:y,children:O.name})}),(0,o.jsx)(T.Text,{as:"address",variant:"info_txt_1",css:ew,children:(0,o.jsx)("span",{className:"bt",children:O.address})}),!c&&m&&(0,o.jsxs)("button",{type:"button",onClick:d,css:[(0,a.flex)("center"),(0,H.mt)(1)],children:[(0,o.jsx)(q.ChevronDownIcon,{wrapperSize:"1.6",size:"1.6",wrapperColor:"transparent"}),(0,o.jsx)(T.Text,{variant:"body_copy_2",css:(0,H.ml)(.5),color:b.colors.secondary,children:"Pokaż na mapie"})]})]})]}),(0,o.jsxs)(eb,{isExpanded:c,css:(0,G.elevation)(0),children:[(0,o.jsx)("div",{css:eT,children:(0,o.jsx)(h.SystemModal.Content,{css:ex,children:c?(0,o.jsx)(Y.OfferDetailLocationMap,{offer:e.selectedOffer,css:ek,disablePoiSwitch:!0,defaultZoom:15,disableClusterMarkers:!0}):(0,o.jsx)("div",{css:ek})})}),c&&(0,o.jsx)("div",{css:e_,children:(0,o.jsx)("button",{type:"button",onClick:d,children:(0,o.jsx)(K.ChevronUpIcon,{wrapperSize:"4.8",size:"2.4",wrapperColor:"white",wrapperType:"circle",css:(0,G.elevation)(2)})})})]}),m&&(0,o.jsx)(el,{openFilters:()=>{(0,J.trackFilterOpenForCategory)({filterCategory:"filters",eventName:"listing_offer_modal_filters"}),p(!0)},openSort:()=>f(!0),modalName:r}),c&&(0,o.jsx)(U.Apla,{variant:"dark",applyOn:(0,o.jsx)("div",{}),css:ej})]})},eb=s.default.div`
    ${({theme:e,isExpanded:t})=>(0,n.css)`
        max-height: ${t?"640px":0};
        transition: max-height ${e.transition.timingFunction} ${e.transition.duration};
        position: absolute;
        left: 0;
        z-index: 999;
        height: 78svh;
        width: 100%;
        background: ${e.colors.gray[100]};
        ${(0,G.elevation)(1)};
        overflow: visible;
    `}
`,ex=(0,n.css)`
    height: 100%;
    width: 100%;
    padding-bottom: ${(0,c.calculateRemSize)(1.5)};
    & .text-wrap {
        height: 100%;
    }
`,ej=(0,n.css)`
    position: fixed;
    inset: auto auto 0 0;
    width: 100%;
    height: 60%;
    z-index: 900;
`,eO=e=>(0,n.css)`
    flex: 0 0 auto;
    position: fixed;
    z-index: 40;
    width: 100%;
    ${(0,d.pt)(1.5)};
    ${(0,d.pb)(1)};
    ${(0,H.mb)(0)};
    background: ${e.colors.gray[100]};
    ${(0,G.elevation)(1)};

    @media (min-width: ${e.breakpoints.md}) {
        background-color: #fff;
    }

    ${(0,l.onDesktop)((0,n.css)`
        position: static;
    `)}
`,eP=e=>(0,n.css)`
    display: flex;
    column-gap: ${(0,c.calculateRemSize)(2)};
    position: relative;

    @media (min-width: ${e.breakpoints.md}) {
        ${(0,d.p)(1.5,0,3,0)};
    }
`,ew=e=>(0,n.css)`
    ${(0,d.p)(0,6,0,0)};
    color: ${e.colors.gray[700]};
    line-height: 20px;
`,eS=e=>(0,n.css)`
    max-width: 8.6rem;
    max-height: 6.4rem;
    ${(0,W.display)("none")};

    & img {
        width: 100%;
        height: auto;
    }

    @media (min-width: ${e.breakpoints.xs}) {
        max-width: 11.2rem;
        max-height: 8.4rem;
    }
`,e_=(0,n.css)`
    position: absolute;
    bottom: 0;
    left: 50%;
    display: flex;
    justify-content: center;
    transform: translate(-50%, 50%);
`,eT=(0,n.css)`
    ${a.flexAbsoluteCenter};
    ${Z.h100};
    overflow: hidden;
`,ek=(0,n.css)`
    ${(0,H.mt)(2.5)}
    height: calc(100% - 20px);
    background-color: #f9f9f9; // to match leaflet map background color
`,eC=(0,n.css)`
    ${(0,H.mb)(.5)};
    max-width: calc(100% - ${(0,c.calculateRemSize)(3)});
`;var eM=r(2009),eI=r(34849),eD=r(49752),e$=r(26822),eA=r(84631),eL=r(94124),eE=r(99363),eR=r(94048),eN=r(1671),ez=r(67823),eF=r(76127),eV=r(59047),eU=r(36357),eG=r(22764);function eB(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}var eH=r(96613),eW=r(11811),eZ=r(99622);function eq(e,t,r,o){var n,s;let[a,l]=(0,i.useState)([]),c=e?Math.ceil(e.count/e.page_size):0,d=e?e.page:1,u=o||d<c;return(0,i.useEffect)(()=>{e&&1===d&&l(e.results),e&&1!==d&&l(t=>[...t,...e.results])},[e]),(0,i.useEffect)(()=>{u&&r&&t()},[r,d,c]),{items:(n=a,s=d,n.map(e=>({data:e,page:s}))),canLoadMore:u,totalPageCount:c}}let eK=()=>(0,o.jsx)("div",{className:"DKIRvTLLPCY84La_",children:(0,o.jsx)(y.Loader,{size:"md"})});var eQ=r(97084);let eY=()=>(0,o.jsxs)("div",{className:"bW8LoItXLoYfQl5A",children:[(0,o.jsx)(eQ.BrandSearchIcon,{size:"6",wrapperSize:"6",wrapperColor:"var(--colors-primary)",wrapperType:"circle",className:"t7gi1MyJ_EoAyiy4"}),(0,o.jsx)(T.Text,{align:"center",variant:"headline_5",mb:1,children:"Nie znaleziono element\xf3w spełniających wybrane kryteria"}),(0,o.jsx)(T.Text,{align:"center",variant:"body_copy_2",children:"Zmień parametry/filtry aby uzyskać więcej wynik\xf3w"})]}),eX=e=>{let{infiniteList:t,listComponent:r,itemComponent:n,handleIsIntersecting:s,loader:a,emptyListInfo:l,listIntersectionContainerId:c}=e,d=(0,i.useRef)(null);(0,i.useEffect)(()=>{if(!d.current)return;let e=new IntersectionObserver(([e])=>{s(e.isIntersecting)},{root:c?document.getElementById(c):null,rootMargin:"30px",threshold:0});return e.observe(d.current),()=>{d.current&&e.unobserve(d.current)}},[c]);let u=!t.canLoadMore&&0===t.items.length;return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(r,{children:t.items.map((e,t)=>(0,o.jsx)(i.Fragment,{children:n({item:e.data,index:t})},`ili${t}`))}),(0,o.jsxs)("div",{ref:d,children:[t.canLoadMore&&a,t.canLoadMore&&!a&&(0,o.jsx)(eK,{}),u&&l,u&&!l&&(0,o.jsx)(eY,{})]})]})};var eJ=r(98986),e0=r(55851);let e1=e=>{var t,r;let{href:i,target:n,onLinkClick:s,children:a,sorted:l,className:c}=e;return(0,o.jsxs)("td",(t=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},e),r=r={className:(0,eJ.cx)(e3,c,l&&e2),children:[i&&(0,o.jsx)("a",{href:i,target:n,onMouseDown:s,className:e5,children:(0,o.jsx)("span",{className:e4,children:"Przejdź do szczeg\xf3ł\xf3w nieruchomości"})}),(0,o.jsx)("div",{className:e6,children:a})]},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t))},e3=(0,e0.css)({minHeight:"54px",border:"0",verticalAlign:"middle",textAlign:"center",padding:"0",position:"relative"}),e2=(0,e0.css)({background:"var(--colors-background-200)"}),e5=(0,e0.css)({position:"absolute",inset:"0",zIndex:"1",textDecoration:"none",color:"inherit"}),e6=(0,e0.css)({position:"relative",zIndex:"2",pointerEvents:"none",display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column",minHeight:"54px","& button, & a":{pointerEvents:"auto"}}),e4=(0,e0.css)({position:"absolute",width:"1px",height:"1px",padding:"0",margin:"-1px",overflow:"hidden",clip:"rect(0, 0, 0, 0)",whiteSpace:"nowrap",borderWidth:"0"}),e9=(0,e0.css)({width:"10%",minWidth:"0"}),e7=(0,e0.css)({width:"15%",minWidth:"0"}),e8=(0,e0.css)({width:"15%",minWidth:"0",md:{width:"20%"}}),te=(0,e0.css)({width:"20%",minWidth:"0",md:{width:"25%"}}),tt=(0,e0.css)({width:"40%",minWidth:"0",md:{width:"30%"}}),tr=[{fieldName:"plan",text:"Rzut",additionalCss:e9},{fieldName:"rooms",text:"Pokoje",additionalCss:e7},{fieldName:"floor",text:"Piętro",additionalCss:e8},{fieldName:"area",text:"Metraż",additionalCss:te},{fieldName:"price",text:"Cena",additionalCss:tt}],to=["number","rooms","area","floor","price"];function ti(e){let{children:t,sort:r,toggleSort:i}=e;return(0,o.jsx)("div",{className:ts,children:(0,o.jsxs)("table",{className:ta,children:[(0,o.jsx)("thead",{children:(0,o.jsx)("tr",{css:tl,children:tr.map(e=>{var t,n;let{fieldName:s,text:a,additionalCss:l}=e,c=to.includes(s);return(0,o.jsx)(T.Text,{as:"th",variant:"body_copy_1",className:(0,eJ.cx)(tc,l,c&&td),onClick:()=>{c&&i(s)},children:(0,o.jsxs)("div",{className:tu,children:[a,c&&(0,o.jsx)(tn,{value:(t=r,n=s,t&&t.fieldName===n?t.value:null)})]})},`mpth${s}`)})})}),(0,o.jsx)("tbody",{children:t})]})})}function tn(e){let{value:t}=e;return(0,o.jsx)("div",{className:(0,e0.css)({opacity:null===t?"0.5":"1",transform:"asc"===t?"rotate(180deg) scale(1.3)":""}),children:(0,o.jsx)(q.ChevronDownIcon,{size:"1.3",fill:"var(--colors-gray-700)"})})}let ts=(0,e0.css)({overflowX:"hidden",mb:3}),ta=(0,e0.css)({width:"100%",borderCollapse:"collapse",tableLayout:"fixed"}),tl=(0,e0.css)({height:"54px"}),tc=(0,e0.css)({border:0,fontWeight:"normal",verticalAlign:"middle",textAlign:"center",padding:0}),td=(0,e0.css)({cursor:"pointer"}),tu=(0,e0.css)({display:"flex",alignItems:"center",justifyContent:"center",columnGap:.5,minHeight:"54px",xs:{columnGap:1}});var tp=r(3063),tf=r(40760),tm=r(63681),tv=r(37682),ty=r(51044),th=r(35299),tg=r(62023),tb=r(16592),tx=r(97299),tj=r(58829),tO=r(16744);function tP(e){let{property:t,index:r,offer:i,handlePlanClick:n,sort:s,trackingMeta:a,amplitudeItemListContext:l,isInModal:c}=e,d=(0,Q.useResponsiveLinkTarget)(),u=(0,tb.getAmplitudeItemListContextWithStaticFallback)({dynamicItemListContext:l,trackingMeta:a}),p=tp.rpAppLink.property.detail.base({vendorSlug:i.vendor.slug,offerSlug:i.slug,offerId:i.id,propertyId:t.id}),f=e=>(0,ty.createOfferListingAmplitudePendingDetailUrl)({url:e,itemId:i.id,propertyId:t.id,itemListContext:l}),m=(0,tv.usePrimaryClick)(e=>{(0,tx.trackPropertySelectItemWithListContext)({offer:i,property:t,index:r,itemListContext:u}),e.currentTarget.href=f(e.currentTarget.href),(0,tj.gtmEventPropertyListClick)("nieruchomosc"),(0,th.hitGTMPropertySelectItem)({offer:i,property:t,listId:a.listId,listName:a.listName}),(0,tO.gtmEventPropertyListPrice)(r+1)});return(0,o.jsxs)("tr",{className:tw,children:[(0,o.jsx)(e1,{href:p,target:d,onLinkClick:m,className:e9,children:t.plan_image_pages&&(0,o.jsx)("button",{className:(0,e0.css)({p:1}),type:"button",onClick:e=>{e.preventDefault(),e.stopPropagation(),n()},children:(0,o.jsx)(er.PropertyPlanIcon,{size:"1.6",wrapperSize:"1.6",wrapperColor:"transparent"})})}),(0,o.jsx)(e1,{href:p,target:d,onLinkClick:m,className:e7,sorted:!!(s&&"rooms"===s.fieldName),children:(0,o.jsx)(T.Text,{variant:"body_copy_2",children:t.rooms})}),(0,o.jsx)(e1,{href:p,target:d,onLinkClick:m,className:e8,sorted:!!(s&&"floor"===s.fieldName),children:(0,o.jsx)(T.Text,{variant:"body_copy_2",children:(0,tg.floorOrFloors)(i.type,t.floors,t.floor)})}),(0,o.jsx)(e1,{href:p,target:d,onLinkClick:m,className:te,sorted:!!(s&&"area"===s.fieldName),children:(0,o.jsx)(T.Text,{variant:"body_copy_2",children:(0,tf.areaFormat)(t.area,{precision:2})})}),(0,o.jsx)(e1,{href:p,target:d,onLinkClick:m,className:tt,sorted:!!(s&&"price"===s.fieldName),children:(0,o.jsx)("div",{onClick:e=>e.stopPropagation(),children:(0,o.jsx)(tm.PropertyViewRedirectButton,{buttonVariant:"highlight_primary",property:t,isInModal:c,link:p,onRedirectClick:e=>{(0,tx.trackPropertySelectItemWithListContext)({offer:i,property:t,index:r,itemListContext:u}),e.currentTarget.href=f(p)}})})})]})}let tw=(0,e0.css)({"&:nth-of-type(odd)":{background:"var(--colors-gray-200)"},"&:nth-of-type(even)":{background:"var(--colors-gray-100)"}});var tS=r(63099),t_=r(32682);function tT(e,t,r,o,i,n,s){try{var a=e[n](s),l=a.value}catch(e){r(e);return}a.done?t(l):Promise.resolve(l).then(o,i)}function tk(e){return function(){var t=this,r=arguments;return new Promise(function(o,i){var n=e.apply(t,r);function s(e){tT(n,o,i,s,a,"next",e)}function a(e){tT(n,o,i,s,a,"throw",e)}s(void 0)})}}function tC(e){var t,r,n,s,a;let{trackingMeta:l,modalName:c,propertiesQuery:d,offer:u,intersectionContainerId:p,amplitudeItemListContext:f}=e,m=(0,R.useAppDispatch)(),v=(0,R.useAppSelector)(e=>e.offerModals[c].sort),[y,h]=(0,i.useState)(!1),g=eq(d.queryData,()=>{m((0,N.loadNextPage)({modalName:c}))},y,d.isUninitialized),{items:b,totalPageCount:x}=g,j=b.length,[O,P]=(0,i.useState)(!1),w=(0,i.useRef)(0),[S,_]=(0,i.useState)(0),T=e=>{(!v||v&&v.fieldName!==e)&&m((0,N.setOfferModalSort)({modalName:c,sort:{fieldName:e,value:"asc"}})),v&&v.fieldName===e&&"desc"===v.value&&m((0,N.setOfferModalSort)({modalName:c,sort:{fieldName:e,value:"asc"}})),v&&v.fieldName===e&&"asc"===v.value&&m((0,N.setOfferModalSort)({modalName:c,sort:{fieldName:e,value:"desc"}}))},k=b[S]?b[S]:b[w.current],C={offer:{geo_point:{coordinates:u.geo_point.coordinates},id:u.id,name:u.name,type:u.type,region:{country:u.region.country,full_name:u.region.full_name,id:u.region.id}},vendor:{id:u.vendor.id,name:u.vendor.name,slug:u.vendor.slug}};return(0,o.jsxs)(o.Fragment,{children:[k&&(0,o.jsx)(tS.PropertyPlanModal,{isOpen:O,property:k.data,offer:u,currentPropertyIndex:S,currentPage:k.page,propertiesOnCurrentPage:b.length,pageCount:x,pageIsLoading:d.isLoading,handleClose:()=>{P(!1)},handleNextClick:e=>tk(function*(){var t;S+1===j&&m((0,N.loadNextPage)({modalName:c})),w.current=t=e,_(t+1)})(),handlePrevClick:e=>tk(function*(){w.current=e,_(e-1)})(),onPlanDownloadClick:()=>{(0,t_.showPropertyPlanView)(t_.ShowPropertyPlanView.PLAN_IMAGE_DOWNLOAD,C.offer,C.vendor)}}),(0,o.jsx)(eX,{infiniteList:g,handleIsIntersecting:e=>{h(e)},listComponent:e=>{let{children:t}=e,r=(0,R.useAppSelector)(e=>e.offerModals[c].sort);return(0,o.jsx)(ti,{sort:r,toggleSort:T,children:t})},itemComponent:(t=u,r=l,n=f,s=e=>{_(e),P(!0)},a=v,e=>{let{item:i,index:l}=e;return(0,o.jsx)(tP,{property:i,index:l,offer:t,sort:a,handlePlanClick:()=>{s(l)},trackingMeta:r,amplitudeItemListContext:n,isInModal:!0})}),listIntersectionContainerId:p})]})}function tM(e){let{children:t,className:r}=e;return(0,o.jsx)("div",{css:tI,className:r,children:t})}let tI=(0,n.css)`
    display: grid;
    grid-template-columns: 1fr;
    column-gap: ${(0,c.calculateRemSize)(1.5)};
    row-gap: ${(0,c.calculateRemSize)(1.5)};
    ${(0,H.mb)(3)};

    ${(0,l.onDesktop)((0,n.css)`
        grid-template-columns: repeat(2, 1fr);
        column-gap: ${(0,c.calculateRemSize)(2)};
        row-gap: ${(0,c.calculateRemSize)(2)};
    `)};

    @media screen and (min-width: 1700px) {
        grid-template-columns: repeat(3, 1fr);
    }
`;var tD=r(76529),t$=r(17866),tA=r(6511),tL=r(4557),tE=r(41944),tR=r(5483),tN=r(19616),tz=r(314),tF=r(95692),tV=r(75183),tU=r(24791),tG=r(48624),tB=r(81181),tH=r(70357);function tW(e){var t;let{property:r,offer:i,className:n,onClick:s}=e,a=(0,V.u)(),l=(0,Q.useResponsiveLinkTarget)(),c=tp.rpAppLink.property.detail.base({vendorSlug:i.vendor.slug,offerSlug:i.slug,offerId:i.id,propertyId:r.id}),d=[{name:"Metraż",text:(0,tf.areaFormat)(r.area,{precision:2})},{name:"Pokoje",text:r.rooms},{name:i.type===tH.OfferType.HOUSE?"Piętra":"Piętro",text:i.type===tH.OfferType.HOUSE?r.floors:0===r.floor?"parter":r.floor}],u=(0,tF.useShouldShowPriceByOfferConfigAndUser)({offerPriceVisibility:r.offer.configuration.price_visibility,vendorPriceVisibility:r.offer.vendor.configuration.price_visibility,vendorId:r.offer.vendor.id}),p=r.offer.currency===tU.Currency.EURO&&r.offer.price_type===tB.OfferPriceType.NETTO?" netto":"";u&&"number"==typeof r.price&&r.price>0&&d.push({name:"Cena",text:(0,tf.priceFormat)(r.price,{unit:`${(0,tG.getCurrency)({currency:r.offer.currency})}`})});let f=(null==(t=r.plan_image)?void 0:t.p_img_375x250)?r.plan_image.p_img_375x250:void 0,m=(0,tV.getPropertyBadgeType)(r);return(0,o.jsx)("a",{href:c,"data-testId":tN.OFFER_TEST_IDS.OFFER_VIEW.PROPERTY_BOX(r.id.toString()),target:l,onMouseDown:s,css:tZ,children:(0,o.jsxs)("div",{css:tq,className:n,children:[(0,o.jsx)(tz.FavoriteButton,{offer:i,property:r,css:t0,display:{type:"icon"},amplitudePlacement:"rp_favourite_offer_modal_tile"}),(0,o.jsxs)("div",{css:tK,children:["reservation"===m&&(0,o.jsx)(et.Badge,{variant:"label_danger",icon:e=>(0,o.jsx)(tL.LockOutlineIcon,{fill:e.fill,css:[e.className,(0,H.mr)(1.5)],wrapperColor:"transparent",wrapperSize:"1.6",size:"1.6"}),children:(0,o.jsx)(T.Text,{as:"span",strong:!0,variant:"info_txt_1",children:"Rezerwacja"})}),"promotion"===m&&(0,o.jsx)(et.Badge,{variant:"label_info",icon:e=>(0,o.jsx)(tE.PercentIcon,{fill:e.fill,css:[e.className,(0,H.mr)(1.5)],wrapperColor:"transparent",wrapperSize:"1.6",size:"1.6"}),children:(0,o.jsx)(T.Text,{variant:"info_txt_2",as:"span",strong:!0,children:"Promocja"})}),"recommended"===m&&(0,o.jsx)(et.Badge,{variant:"label_success",icon:e=>(0,o.jsx)(tR.LikeIcon,{fill:e.fill,css:[e.className,(0,H.mr)(1.5)],wrapperColor:"transparent",wrapperSize:"1.6",size:"1.6"}),children:(0,o.jsx)(T.Text,{as:"span",strong:!0,variant:"info_txt_1",children:"Polecane"})})]}),r.external_plan_url?(0,o.jsx)(t$.CenteredImage,{css:tJ,src:r.external_plan_url,alt:i.name,width:375,height:250,breakpoints:[{mediaWidth:"0",width:"304px",height:"272px"},{mediaWidth:a.breakpoints.sm,width:"232px",height:"200px"}]}):(0,o.jsx)(t$.CenteredImage,{css:tX,src:f,alt:i.name,width:375,height:250,breakpoints:[{mediaWidth:"0",height:"200px",width:"100%"}]}),(0,o.jsx)("ul",{css:tQ,children:d.map((e,t)=>{let r="Cena"===e.name?`${e.name}${p}`:e.name;return(0,o.jsxs)("li",{css:tY,children:[(0,o.jsx)(T.Text,{css:(0,H.mb)(.5),variant:"info_txt_3",color:a.colors.gray[700],children:r}),(0,o.jsx)(T.Text,{variant:"info_txt_1",strong:"Cena"===e.name,children:e.text})]},`itl${t}`)})})]})})}let tZ=(0,n.css)`
    &:hover {
        color: inherit;
    }
`,tq=(0,n.css)`
    ${(0,G.elevation)(2)};
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    row-gap: ${(0,c.calculateRemSize)(2)};
    background-color: #fff;
    transition: box-shadow 0.2s ease-in-out;
    ${(0,tA.borderRadius)(2)};
    ${(0,d.p)(2,1)};
    height: 100%;

    &:hover {
        ${(0,G.elevation)(3)}
    }
`,tK=(0,n.css)`
    position: absolute;
    top: ${(0,c.calculateRemSize)(1)};
    left: ${(0,c.calculateRemSize)(1)};
    z-index: ${30};
`,tQ=(0,n.css)`
    padding: 0;
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    column-gap: ${(0,c.calculateRemSize)(2)};
`,tY=(0,n.css)`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
`,tX=(0,n.css)`
    flex: 1 0 auto;
`,tJ=(0,n.css)`
    flex: 1 0 auto;

    img {
        max-width: 100%;
        max-height: 100%;
    }
`,t0=(0,n.css)`
    position: absolute;
    top: ${(0,c.calculateRemSize)(1)};
    right: ${(0,c.calculateRemSize)(1)};
    z-index: ${30};
`;function t1(e){let{property:t,offer:r,index:i,trackingMeta:n,amplitudeItemListContext:s}=e,a=(0,tb.getAmplitudeItemListContextWithStaticFallback)({dynamicItemListContext:s,trackingMeta:n}),l=(0,tv.usePrimaryClick)(e=>{(0,tj.gtmEventPropertyListClick)("rzut"),(0,tx.trackPropertySelectItemWithListContext)({offer:r,property:t,index:i,itemListContext:a}),e.currentTarget.href=(0,ty.createOfferListingAmplitudePendingDetailUrl)({url:e.currentTarget.href,itemId:r.id,propertyId:t.id,itemListContext:s}),(0,th.hitGTMPropertySelectItem)({offer:r,property:t,listName:n.listName,listId:n.listId}),"listing"===n.source?tD.offerBoxTracking.gtm.investTileOfferModal(i):tD.offerBoxTracking.gtm.investAdditionalOfferModal(i)});return(0,o.jsx)(tW,{property:t,offer:r,onClick:l})}function t3(e){var t,r,n;let{trackingMeta:s,modalName:a,propertiesQuery:l,offer:c,intersectionContainerId:d,amplitudeItemListContext:u}=e,p=(0,R.useAppDispatch)(),[f,m]=(0,i.useState)(!1),v=eq(l.queryData,()=>{p((0,N.loadNextPage)({modalName:a}))},f,l.isUninitialized);return(0,o.jsx)(h.SystemModal.Content,{css:t2,children:(0,o.jsx)(eX,{listComponent:tM,itemComponent:(t=c,r=s,n=u,e=>{let{item:i,index:s}=e;return(0,o.jsx)(t1,{property:i,offer:t,index:s,trackingMeta:r,amplitudeItemListContext:n})}),infiniteList:v,listIntersectionContainerId:d,handleIsIntersecting:e=>{m(e)}})})}let t2=(0,n.css)`
    ${(0,l.onDesktop)((0,n.css)`
        ${(0,d.p)(0)}
    `)}
`;var t5=r(32693);function t6(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}function t4(e,t){return t=null!=t?t:{},Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(t)).forEach(function(r){Object.defineProperty(e,r,Object.getOwnPropertyDescriptor(t,r))}),e}function t9(e){var t;let{modalName:r,offerDetails:n,userPreferenceFilters:s,filtersModalOpened:a,handleFiltersModalVisibility:l,handleSortModalVisibility:c,mobileSortModalOpened:d}=e,u=(0,i.useRef)(null),p=(0,R.useAppDispatch)(),{isMobile:f}=(0,g.useUserDevice)(),{putPreferences:m}=(0,eR.useHomeMatchPreferencesStorage)(),v=(0,R.useAppSelector)(e=>e.offerModals[r].type),y=(0,R.useAppSelector)(e=>(e=>{var t;let r=(null==e?void 0:e.value)==="desc"?"-":"",o=`${r}${null==e?void 0:e.fieldName}`;return(null==(t=eL.propertyListSortOptions.find(e=>e.slug===o))?void 0:t.value)||eN.SortOptionsValues.LOWEST_PRICE})(e.offerModals[r].sort)),b=(0,R.useAppSelector)(e=>e.offerModals[r].filters),x=(0,R.useAppSelector)(e=>e.offerModals[r].filters.rooms),j=function(e,t){var r,o;let i=(0,R.useAppSelector)(t=>t.offerModals[e].isOpen),n=(0,R.useAppSelector)(t=>t.offerModals[e].offerId),s=(0,R.useAppSelector)(t=>t.offerModals[e].sort),a=(0,R.useAppSelector)(t=>t.offerModals[e].page),l=(0,R.useAppSelector)(t=>t.offerModals[e].pageSize),c=(0,R.useAppSelector)(t=>t.offerModals[e].filters),d={area:eF.FormFieldType.InputRange,rooms:eF.FormFieldType.SelectRangeNumber,floor_choices:eF.FormFieldType.MultiCheckbox,house_storeys:eF.FormFieldType.MultiCheckbox,price:eF.FormFieldType.InputRange},u=eB({},(0,eV.toQueryValues)(d,c)),p=eB((r=eB({},eG.offerDetailPropertiesListConstraints),o=o={offer:n,page:a,page_size:l,sort:s?function(e){let t="asc"===e.value?"":"-";return`${t}${e.fieldName}`}(s):s},Object.getOwnPropertyDescriptors?Object.defineProperties(r,Object.getOwnPropertyDescriptors(o)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(o)).forEach(function(e){Object.defineProperty(r,e,Object.getOwnPropertyDescriptor(o,e))}),r),u,function(e){if(!e)return{};let{construction_end_date:t,floor_choices:r}=e,o={};return t&&(o.construction_end_date=parseInt(t,10)),r&&(o.floor_choices=r.map(e=>parseInt(e,10))),o}(t)),{currentData:f,isLoading:m,isFetching:v,isUninitialized:y}=(0,eU.useGetPropertyListQuery)(p,{skip:!i});return{queryData:f,isLoading:m||v,isUninitialized:y}}(r,s),O=null==n?void 0:n.type,P=O===eD.OfferType.HOUSE,w=O===eD.OfferType.FLAT,S=w?b.floor_choices:b.house_storeys;(0,i.useEffect)(()=>{p((0,N.resetPropertyList)({modalName:r}))},[v]);let _=(0,R.useAppSelector)(e=>e.offerModals[r].gtmSource),T=(0,R.useAppSelector)(e=>e.offerModals[r].amplitudeItemListContext),k=(0,i.useMemo)(()=>({listName:`Zobacz ${(0,ez.getOfferTypeNamePlural)(n.type)}`,listId:`zobacz_${(0,ez.getOfferTypeNamePlural)(n.type)}`,source:_}),[n.type,_]);(0,i.useEffect)(()=>{u.current&&(u.current.scrollTop=0)},[n.id]);let{hasBeenAccumulated:C,accumulatedResults:M}=function({results:e,isLoading:t,accumulationTime:r=5e3}){let[o,n]=(0,i.useState)([]),[s,a]=(0,i.useState)(!1),[l,c]=(0,i.useState)(!1),d=(0,i.useRef)(null),u=(0,i.useRef)([]);return(0,i.useEffect)(()=>{!l&&!t&&(null==e?void 0:e.length)&&e!==u.current&&(n(t=>[...t,...e]),a(!0),u.current=e)},[t,e,l]),(0,i.useEffect)(()=>(d.current&&clearTimeout(d.current),!l&&s&&o.length>0&&(d.current=setTimeout(()=>{c(!0)},r)),()=>{d.current&&clearTimeout(d.current)}),[s,o,r,l]),(0,i.useEffect)(()=>()=>{d.current&&clearTimeout(d.current)},[]),{accumulatedResults:o,hasBeenAccumulated:l}}({results:null==(t=j.queryData)?void 0:t.results,accumulationTime:3e3,isLoading:j.isLoading});(0,i.useEffect)(()=>{C&&M.length&&(0,eW.hitGTMPropertyViewItemList)({offer:n,properties:M,listName:k.listName,listId:k.listId})},[C,M]);let I=f?"offer-modal-layout":"offer-modal-list";return(0,o.jsxs)("div",{css:t8,children:[(0,o.jsx)(h.SystemModal.Content,{css:ri,children:(0,o.jsxs)("div",{css:rt,children:[(0,o.jsxs)("div",{css:rr,children:[(0,o.jsx)(t5.RoomFilter,{css:ro,initialValue:x,trackingParams:{eventName:"listing_offer_modal_filters"},onConfirm:e=>{n.region.country===eI.Country.POLAND&&m({rooms:e}),(0,eM.hitUserSegmentRooms)(e),p((0,N.setOfferModalFilters)({modalName:r,filters:t4(t6({},b),{rooms:e})}))},handleClear:()=>{p((0,N.setOfferModalFilters)({modalName:r,filters:t4(t6({},b),{rooms:{lower:"",upper:""}})}))}}),(0,o.jsx)(eE.AreaFilter,{css:ro,initialValue:b.area,trackingParams:{eventName:"listing_offer_modal_filters"},onConfirm:e=>{p((0,N.setOfferModalFilters)({modalName:r,filters:t4(t6({},b),{area:e})}))},handleClear:()=>{p((0,N.setOfferModalFilters)({modalName:r,filters:t4(t6({},b),{area:{lower:"",upper:""}})}))}}),(w||P)&&(0,o.jsx)(eZ.FloorFilter,{css:ro,id:"offer-modal-floors",initialValue:S,offerType:O,trackingParams:{eventName:"listing_offer_modal_filters"},onConfirm:e=>{p((0,N.setOfferModalFilters)({modalName:r,filters:t4(t6({},b),{[w?"floor_choices":"house_storeys"]:e})}))},handleClear:()=>{p((0,N.setOfferModalFilters)({modalName:r,filters:t4(t6({},b),{[w?"floor_choices":"house_storeys"]:[]})}))}})]}),!f&&(0,o.jsx)(el,{openFilters:()=>{l(!0)},openSort:()=>{c(!0)},modalName:r})]})}),(0,o.jsxs)("div",{id:"offer-modal-list",css:re,ref:u,children:["tiles"===v&&(0,o.jsx)(t3,{modalName:r,offer:n,propertiesQuery:j,intersectionContainerId:I,trackingMeta:k,amplitudeItemListContext:T}),"table"===v&&(0,o.jsx)(tC,{modalName:r,propertiesQuery:j,offer:n,intersectionContainerId:I,trackingMeta:k,amplitudeItemListContext:T})]}),(0,o.jsx)(e$.PropertyListFiltersModal,{offerType:O,filters:b,isOpen:a,handleClose:e=>{if(l(!1),!e)return;p((0,N.setOfferModalFilters)({modalName:r,filters:eH.offerModalInitialState.filters}));let t={1:e.floorGround,2:e.floorGroundWithGarden,3:e.floorOneToFour,4:e.floorFivePlus,5:e.floorLast,6:e.floorLastWithTerrace},o=Object.keys(t).filter(e=>!!t[parseInt(e)]).map(e=>parseInt(e)),i=t6({rooms:b.rooms,area:b.area},O===eD.OfferType.FLAT?{floor_choices:o}:{house_storeys:o}),{categories:n,options:s}=(0,J.getMobileFiltersLabelForTracking)(i,O);(0,J.trackFilterClearForCategories)({eventName:"listing_offer_modal_filters",filterCategory:n,customLabel:s||void 0})},handleConfirm:e=>{l(!1);let t={1:e.floorGround,2:e.floorGroundWithGarden,3:e.floorOneToFour,4:e.floorFivePlus,5:e.floorLast,6:e.floorLastWithTerrace},o=Object.keys(t).filter(e=>!!t[parseInt(e)]).map(e=>parseInt(e)),i=t6({area:e.area,rooms:e.rooms},w?{floor_choices:o}:{house_storeys:o});if(p((0,N.setOfferModalFilters)({modalName:r,filters:i})),f){let{categories:e,options:t}=(0,J.getMobileFiltersLabelForTracking)(i,O);e&&(0,J.trackFilterApplyForCategories)({eventName:"listing_offer_modal_filters",filterCategory:e,customLabel:t||void 0})}}}),(0,o.jsx)(eA.PropertyListSortOptionsModal,{onClear:()=>{let e=t7(eN.SortOptionsValues.LOWEST_PRICE);p((0,N.setOfferModalSort)({modalName:r,sort:e})),c(!1)},onSave:e=>{f&&c(!1);let t=t7(e);p((0,N.setOfferModalSort)({modalName:r,sort:t}))},onClose:()=>{c(!1)},isOpen:d,defaultValue:y||eN.SortOptionsValues.LOWEST_PRICE})]})}let t7=e=>{let t=eL.propertyListSortOptions.find(t=>t.value===e);return t?t.slug.includes("-")?{fieldName:t.slug.slice(1),value:"desc"}:{fieldName:t.slug,value:"asc"}:null},t8=(0,n.css)`
    width: 100%;
    position: relative;

    ${(0,l.onDesktop)((0,n.css)`
        display: flex;
        flex-direction: column;
    `)}
`,re=(0,n.css)`
    ${(0,l.onDesktop)((0,n.css)`
        overflow-y: auto;
        overflow-x: hidden;

        /*
          A hacky way to achieve horizontal overflow: visible (for shadows)
         */
        margin: 0 -${(0,c.calculateRemSize)(2)};
        padding: 0 ${(0,c.calculateRemSize)(2)};
    `)}
`,rt=(0,n.css)`
    display: flex;
    justify-content: space-between;
    ${(0,d.pv)(2)}

    ${(0,l.onDesktop)((0,n.css)`
        display: flex;
        flex-direction: column;
        row-gap: ${(0,c.calculateRemSize)(3)};
    `)}
`,rr=(0,n.css)`
    display: none;

    ${(0,l.onDesktop)((0,n.css)`
        display: flex;
        flex: 1 1 auto;
        column-gap: ${(0,c.calculateRemSize)(2)};
    `)}
`,ro=(0,n.css)`
    flex: 1 1 33%;
    min-width: 0;
`,ri=(0,n.css)`
    display: none;
    ${(0,l.onDesktop)((0,n.css)`
        display: block;
        ${(0,d.p)(0)}
    `)}
`;var rn=r(84136),rs=r(71953),ra=r(62363),rl=r(64097);let rc=(0,ra.pluralize)(["inwestycja","inwestycje","inwestycji"]),rd=e=>{let{offersQuery:t,modalName:r,onNextOffer:i,onPrevOffer:n}=e,s=(0,V.u)(),{isMobile:a}=(0,g.useUserDevice)(),l=(0,R.useAppDispatch)(),c=(0,R.useAppSelector)(e=>e.offerModals[r].latestNavUsed),d=t.page,u=t.pageSize,{selectedOffer:p,offersWithPosition:f,offersStartingPosition:m}=eh({offers:t.data,page:d,pageSize:u,modalName:r});if(!p)return null;let v=p.position+1,y=f.find(e=>e.position===v),h=p.position-1,b=f.find(e=>e.position===h),x=d>1?m:0,j=x+u+1,O=t.count,P=p.position+1,w=null==y?void 0:y.data.configuration.pre_sale,S=null==b?void 0:b.data.configuration.pre_sale,_=P<O&&!(w&&v+1===O),k=P>1&&!(S&&h<=0),C=1===O,M=p.data.configuration.pre_sale,I=()=>{v+1===j&&l((0,N.setModalQueryParams)({modalName:r,listingPage:d+1,listingPageSize:u})),y&&(null==i||i(y.id),l((0,N.navToNextModal)({modalName:r,offerId:y.id})))},D=()=>{h+1===x&&l((0,N.setModalQueryParams)({modalName:r,listingPage:d-1,listingPageSize:u})),b&&(null==n||n(b.id),l((0,N.navToPrevModal)({modalName:r,offerId:b.id})))};return M&&(c===rl.OfferModalLatestNavType.NEXT&&I(),c===rl.OfferModalLatestNavType.PREV&&D()),(0,o.jsxs)("div",{css:ru,children:[!C&&-1!==p.position&&(0,o.jsx)("button",{type:"button",disabled:!k,onClick:D,css:rm,children:(0,o.jsx)(rn.ChevronLeftIcon,{size:a?"1.6":"3.6",wrapperSize:a?"3.2":"6.4",fill:k?s.colors.secondary:s.colors.gray[700],wrapperColor:k?s.colors.primary:s.colors.gray[100]})}),(0,o.jsxs)(T.Text,{variant:"body_copy_2",color:a?void 0:"white",align:a?void 0:"center",css:rp,children:[P,"/",O," ",rc(O)]}),!C&&(0,o.jsx)("button",{type:"button",disabled:!_,onClick:I,css:rf,children:(0,o.jsx)(rs.ChevronRightIcon,{size:a?"1.6":"3.6",wrapperSize:a?"3.2":"6.4",fill:_?s.colors.secondary:s.colors.gray[700],wrapperColor:_?s.colors.primary:s.colors.gray[100]})})]})},ru=(0,n.css)`
    position: fixed;
    inset: auto 0 0;
    background-color: #fff;
    z-index: 30;
    ${B.w100};
    ${(0,a.flex)("center","center")};
    gap: ${(0,c.calculateRemSize)(3)};
    min-height: ${(0,c.calculateRemSize)(6)};
    max-height: ${(0,c.calculateRemSize)(6)};
    ${(0,G.elevation)(1)};

    ${(0,l.onDesktop)((0,n.css)`
        background-color: transparent;
        ${(0,G.elevation)(0)};
        position: initial;
        min-height: 0;
        max-height: 0;
    `)}
`,rp=(0,n.css)`
    ${(0,l.onDesktop)((0,n.css)`
        position: absolute;
        inset: 0 0 auto 0;
        transform: translateY(-100%);
        line-height: ${(0,c.calculateRemSize)(5)};
    `)}
`,rf=(0,n.css)`
    ${(0,l.onDesktop)((0,n.css)`
        position: absolute;
        z-index: 20;
        inset: 50% -${(0,c.calculateRemSize)(9)} auto auto;
        transform: translate(100%, -100%);
    `)}
`,rm=(0,n.css)`
    ${(0,l.onDesktop)((0,n.css)`
        position: absolute;
        z-index: 20;
        inset: 50% auto auto -${(0,c.calculateRemSize)(9)};
        transform: translate(-100%, -100%);
    `)}
`,rv=r(73680);function ry(e){var t,r,n,s,l;let{modalName:c,initialQueryParams:d,userPreferencePropertyFilters:u,offersQuery:p,onClose:f}=e,m=(0,R.useAppDispatch)(),{isMobile:b}=(0,g.useUserDevice)(),x=(0,i.useRef)(null),[O,P]=(0,i.useState)(!1),[w,S]=(0,i.useState)(null),[_,T]=(0,i.useState)(!1),[k,M]=(0,i.useState)(!1),I=(0,R.useAppSelector)(e=>e.offerModals[c].isOpen),D=(0,R.useAppSelector)(e=>e.offerModals[c].offer),$=(0,R.useAppSelector)(e=>e.offerModals[c].offerId),A=(0,R.useAppSelector)(e=>e.offerModals[c].sort),L=(0,R.useAppSelector)(e=>e.offerModals[c].filters),E=(0,R.useAppSelector)(e=>e.offerModals[c].sourceSection),V=(0,R.useAppSelector)(e=>e.offerModals[c].page),U=(0,R.useAppSelector)(e=>e.offerModals[c].type),G=D||p.data.find(e=>e.id===$),{isOpen:B}=j({routeParam:"offer-modal",value:c,idOpenStoreState:I,disableOpenAction:!$,removeRouteParamFromUrlOnFirstMount:!0,setModalState:e=>{e?m((0,N.showOfferModal)({modalName:c,offer:D||p.data[0],offerId:(null==D?void 0:D.id)||p.data[0].id,filters:L,sourceSection:E||void 0})):m((0,N.hideOfferModal)({modalName:c}))}});(0,i.useEffect)(()=>{if(B&&d){let{listingPage:e,listingPageSize:t}=d;m((0,N.setModalQueryParams)({modalName:c,listingPage:e,listingPageSize:t}))}},[B]),(0,i.useEffect)(()=>{let e=x.current;if(e&&e<p.page&&p.isSuccess&&!p.isLoading){let e=p.data[0].id;m((0,N.navToNextModal)({modalName:c,offerId:e}))}if(e&&e>p.page&&p.isSuccess&&!p.isLoading){let e=p.data[p.data.length-1].id;m((0,N.navToPrevModal)({modalName:c,offerId:e}))}p.isSuccess&&!p.isLoading&&(x.current=p.page)},[p.page,p.isSuccess,p.isLoading]);let H=e=>{T(e)},W=e=>{M(e)};return(0,o.jsxs)(h.SystemModal,{css:rh,isOpen:B,onModalClose:()=>{f&&f({filters:L,sort:A,page:V}),P(!1),m((0,N.setOfferModalType)({modalName:c,type:"tiles"})),m((0,N.hideOfferModal)({modalName:c}))},variant:b?"fit":"medium",closeButtonStyle:rg,children:[p.isLoading&&(0,o.jsx)("div",{css:a.flexAbsoluteCenter,children:(0,o.jsx)(y.Loader,{size:"md"})}),p.isSuccess&&G&&(0,o.jsxs)(F.OfferModalLayout,{id:"offer-modal-layout",mobileImageOpened:O,children:[(0,o.jsx)(eg,{modalName:c,offers:p.data,paginationQuery:{page:p.page,pageSize:p.pageSize},isExpanded:O,toggleExpand:()=>{P(!O)},onHeightUpdate:e=>{S(e)},selectedOffer:G,handleFiltersModalVisibility:H,handleSortModalVisibility:W}),w&&(0,o.jsxs)(rb,{headerHeight:w,children:[!b&&(0,o.jsxs)("div",{css:rO,children:[(0,o.jsx)(v.Image,{css:rj,src:null==(t=G.main_image)?void 0:t.m_img_750,width:"352px",height:"200px",alt:`${G.vendor.name}`,imageStyle:r_}),(0,o.jsxs)("div",{css:rP,children:[(0,o.jsx)(v.Image,{css:rw,alt:"lokalizacja inwestycji",width:"100%",height:"100%",src:null==(r=G.map_image)?void 0:r.m_img_352x647,src2x:null==(n=G.map_image)?void 0:n.m_img_704x1294,src3x:null==(s=G.map_image)?void 0:s.m_img_1056x1941,imageStyle:rT}),(null==(l=G.map_image)?void 0:l.m_img_352x647)&&(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(v.Image,{src:rv,alt:"",width:"30",height:"38",css:rS}),(0,o.jsx)(C,{})]})]})]}),(0,o.jsx)("div",{css:rx,children:(0,o.jsx)(t9,{modalName:c,userPreferenceFilters:u,offerDetails:G,handleFiltersModalVisibility:H,handleSortModalVisibility:W,filtersModalOpened:_,mobileSortModalOpened:k})})]}),(0,o.jsx)(rd,{offersQuery:p,selectedOffer:G,modalName:c,onNextOffer:e=>{(0,z.hitOfferModalArrowGtm)("right",U)},onPrevOffer:e=>{(0,z.hitOfferModalArrowGtm)("left",U)}})]})]})}let rh=e=>(0,n.css)`
    inset: 0;
    background-color: ${e.colors.gray[100]};

    ${(0,l.onDesktop)((0,n.css)`
        inset: ${(0,c.calculateRemSize)(5)} auto;
        overflow: visible;
        width: 960px;
        background-color: #fff;
    `)};

    @media screen and (min-width: 1700px) {
        width: 1238px;
    }
`,rg={zIndex:50,inset:`${(0,c.calculateRemSize)(1.5)} ${(0,c.calculateRemSize)(1.5)} auto auto`,"@media (min-width: 1024px)":{inset:`${(0,c.calculateRemSize)(4)} ${(0,c.calculateRemSize)(3)} auto auto`}},rb=s.default.div`
    ${({headerHeight:e})=>(0,n.css)`
        padding-top: calc(${e}px + ${(0,c.calculateRemSize)(1)});
        ${(0,d.pb)(6)};

        ${(0,l.onDesktop)((0,n.css)`
            display: flex;
            column-gap: ${(0,c.calculateRemSize)(2)};
            ${(0,d.p)(0,3,4,3)}
            overflow: visible;
            min-height: 0;
        `)}
    `}
`,rx=e=>(0,n.css)`
    flex: 1 1 auto;
    overflow: scroll;
    display: flex;
    background: ${e.colors.gray[100]};

    @media (min-width: ${e.breakpoints.md}) {
        background-color: #fff;
    }

    & > div {
        flex: 1;
    }

    ${(0,l.onDesktop)((0,n.css)`
        overflow: visible;
        background: transparent;
        min-width: 0;
    `)}
`,rj=(0,n.css)`
    min-height: 200px;
`,rO=(0,n.css)`
    ${(0,a.flex)("flex-start","flex-start")};
    ${(0,a.flexDirection)("column")};
    max-width: 352px;
    ${u};
`,rP=(0,n.css)`
    position: relative;
    ${(0,p.mt)(1.5)};
    height: Calc(100% - 200px - ${(0,c.calculateRemSize)(1.5)});
    ${m};
    max-height: 647px;
`,rw=(0,n.css)`
    ${u};
    ${m};
`,rS=(0,n.css)`
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
`,r_={objectFit:"cover",objectPosition:"bottom"},rT={objectFit:"cover",objectPosition:"center"}},38101:function(e,t,r){r.r(t),r.d(t,{OfferDetailLocationMap:()=>Y});var o=r(52903),i=r(2784),n=r(28165),s=r(49111),a=r(83397),l=r(66770),c=r(25598),d=r(95420),u=r(39754),p=r(86330),f=r(83140),m=r(89082),v=r(60012),y=r(29151),h=r(89143),g=r(6511),b=r(93148),x=r(30583),j=r(60338),O=r(48601),P=r(580),w=r(69751),S=r(64462),_=r(19616),T=r(96665),k=r(85866),C=r(88703);let M={location:{label:"",value:"",coordinates:[]}},I=O.object({location:O.mixed().test({message:T.validationMessages.required,test:e=>(0,k.isValidLocationObject)(e)})}),D=e=>(0,o.jsx)(j.Formik,{initialValues:function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},M),validationSchema:I,onSubmit:(t,{setSubmitting:r})=>{if(e.targetCoords){var o;let{location:{label:i}}=t,{lat:n,lng:s}=(0,S.convertToLatLngLiteralOfPoland)(t.location.coordinates),{lng:a,lat:l}=(0,S.convertToLatLngLiteralOfPoland)(e.targetCoords),c=(0,w.countDistance)({lat:n,lng:s},{lat:l,lng:a});r(!1);let d={id:Date.now(),name:"Moje miejsce",distance:c,lat:n,lng:s,tags:{address:i}};null==(o=e.onChange)||o.call(e,d)}},enableReinitialize:!0,children:e=>(0,o.jsxs)("form",{onSubmit:e.handleSubmit,children:[(0,o.jsx)("div",{children:(0,o.jsx)(C.PlacesAutocomplete,{name:"location",placeholder:"Wpisz adres",allowEditLastValue:!0,disableDropdownIndicator:!0})}),(0,o.jsx)(P.Button,{css:[l.w100,(0,s.mt)(2)],type:"submit",disabled:e.isSubmitting,variant:"outlined_secondary",dataTestId:_.OFFER_TEST_IDS.OFFER_VIEW.CHECK_TRAVEL_TIME_BUTTON,children:"Sprawdź czas dojazdu"})]})}),$=e=>{var t;let[r,n]=(0,i.useState)(!1),s=null==(t=e.offer)?void 0:t.geo_point.coordinates;return(0,o.jsxs)("div",{css:A,className:e.className,children:[e.hideHeader?null:(0,o.jsxs)("div",{css:L,children:[(0,o.jsx)(p.Text,{as:"span",variant:"headline_6",children:"Moje miejsce"}),e.disableCollapsible?null:(0,o.jsx)("span",{css:E,onClick:()=>n(e=>!e),children:r?(0,o.jsx)(b.ChevronDownIcon,{size:"2"}):(0,o.jsx)(x.ChevronUpIcon,{size:"2"})})]}),(0,o.jsx)("div",{css:r&&!e.disableCollapsible?R:null,children:(0,o.jsx)("div",{css:N,children:(0,o.jsx)(D,{onChange:e.onChange,targetCoords:s})})})]})},A=e=>(0,n.css)`
    background-color: #fff;
    width: 100%;
    ${(0,s.mt)(6)};

    @media (min-width: ${e.breakpoints.md}) {
        width: 26.4rem;
        ${(0,h.elevation)()};
        ${(0,g.borderRadius)(2)};
        ${(0,u.p)(2)};
        ${(0,s.mt)(0)};
    }
`,L=(0,n.css)`
    ${(0,a.flex)("center","space-between")};
    user-select: none;
    ${(0,s.mb)(3)};
`,E=e=>(0,n.css)`
    cursor: pointer;

    @media (max-width: ${e.breakpoints.md}) {
        display: none;
    }
`,R=(0,n.css)`
    height: 0;
    overflow: hidden;
`,N=e=>(0,n.css)`
    @media (max-width: ${e.breakpoints.md}) {
        ${(0,u.pb)(4)};
        ${(0,s.mb)(3)};
    }
`;var z=r(86557),F=r(6982),V=r(95397),U=r(45706),G=r(73916),B=r(67108),H=r(11646),W=r(34978);let Z=r(43380);var q=r(29043),K=r(87630),Q=r(74816);let Y=e=>{var t,r,n;let{offer:a}=e,[l,c]=(0,i.useState)(z.POI_DISTANCE_DEFAULT_VALUE),{markers:d,onSinglePoiChange:u}=(e=>{let t=(0,V.useDispatch)(),{getPoiDirections:r}=(0,W.useGooglePoiTravelDirections)(),[o,n]=(0,i.useState)([]);return{markers:o,onSinglePoiChange:o=>{let i=[(0,B.createGetOsmPoiMarker)((e,r)=>t((0,G.setActivePoi)(e,r)),null==e?void 0:e.geo_point.coordinates)(o,H.PoiType.USER,Z,{listenToActivePoiDirections:!0})];r(o,H.PoiType.USER,(null==e?void 0:e.geo_point.coordinates)||[0,0],U.TravelMode.DRIVING),n(i)}}})(a),h=(0,K.getHasCountryPois)(a.region.country),{offerAdditionalPois:g,defaultPoiTypes:b,mapBottomSlot:x}=(0,F.useMapNearbyOffersPois)({baseOffer:{id:e.offer.id,type:e.offer.type,stats:"stats"in e.offer&&e.offer.stats?{ranges_area_min:"ranges_area_min"in e.offer.stats?e.offer.stats.ranges_area_min:void 0,ranges_area_max:"ranges_area_max"in e.offer.stats?e.offer.stats.ranges_area_max:void 0,rooms:"rooms"in e.offer.stats?e.offer.stats.rooms:void 0}:void 0},distance:l,showPropertyNumberOnMarker:!!e.property}),j=(0,f.useElementInteractionObserver)({callback:()=>{q.poiAnalytics.gtm.mapEvent({action:q.PoiGTMModalAction.MAP_FIRST_INTERACTION})},once:!0});return(0,o.jsx)("div",{ref:j,css:X,className:e.className,children:(0,o.jsx)(m.OpenStreetMapsWithPoi,{offer:(r=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},e.offer),n=n={geo_area:{coordinates:{coordinates:"geo_area"in a?null==(t=a.geo_area)?void 0:t.coordinates:[]}}},Object.getOwnPropertyDescriptors?Object.defineProperties(r,Object.getOwnPropertyDescriptors(n)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(n)).forEach(function(e){Object.defineProperty(r,e,Object.getOwnPropertyDescriptor(n,e))}),r),viewType:e.property?Q.ViewType.PROPERTY:Q.ViewType.OFFER,polygon:e.area&&e.area.polygon,region:e.area&&e.area.region,disableInitiallyOpenedPoiId:!0,mapConfig:{scrollWheelZoom:!1,fitBounds:!0,fitBoundsDefaultZoom:e.defaultZoom,maxZoom:18},mobilePoiModalTriggerPosition:"center",customMarkers:d,customPoiMarkers:g,clusterMarkers:!e.disableClusterMarkers,disablePoiSwitch:!h||e.disablePoiSwitch,initialPoiTypes:b,mapBottomSlot:x,css:ei,onFullscreenClick:e.onFullscreenClick,drawPoiDistance:!0,onDistanceChange:c,showTransportLines:!0,children:({setCheckedPoiTypes:e,checkedPoiTypes:t,map:r,poiDistance:i,setPoiDistance:n})=>(0,o.jsxs)("div",{css:J,children:[(0,o.jsx)("div",{css:ee,children:r}),h&&(0,o.jsxs)("div",{css:et,children:[(0,o.jsx)(p.Text,{as:"div",variant:"mini_header",children:"Ważne miejsca"}),(0,o.jsx)(v.PoiSwitcher,{checkedPoiTypes:t,onChange:e,hideHeader:!0,disableCollapsible:!0,css:er}),(0,o.jsx)(p.Text,{as:"div",variant:"mini_header",css:[(0,s.mt)(1),(0,s.mb)(1)],children:"Promień"}),(0,o.jsx)(y.PoiSwitcherDistance,{value:i,onChange:n}),(0,o.jsx)(p.Text,{as:"div",variant:"mini_header",css:[(0,s.mt)(3)],children:"Moje miejsce"}),(0,o.jsx)($,{onChange:u,offer:a,hideHeader:!0,disableCollapsible:!0,css:eo})]})]})})})},X=e=>(0,n.css)`
    position: relative;
    height: 58rem;

    @media (min-width: ${e.breakpoints.md}) {
        height: 58.5rem; // to avoid scroll on map sidebar with default params
    }

    @media (min-width: ${e.breakpoints.lg}) {
        height: 68rem;
    }
`,J=(0,n.css)`
    ${(0,a.flex)()};
    ${l.w100};
    ${c.h100};
`,ee=(0,n.css)`
    position: relative;
    flex: 1 1 100%;
`,et=(0,n.css)`
    display: none;

    ${(0,d.onDesktop)((0,n.css)`
        display: block;
        background-color: #fff;
        flex: 0 0 30rem;
        ${(0,u.p)(3,2)};
        overflow: auto;
    `)};
`,er=(0,n.css)`
    ${(0,d.onDesktop)((0,n.css)`
        box-shadow: none;
        border-radius: 0;
        width: 100%;
    `)};
`,eo=(0,n.css)`
    ${(0,d.onDesktop)((0,n.css)`
        box-shadow: none;
        border-radius: 0;
        width: 100%;
        ${(0,u.p)(2,0,0,0)};
    `)};
`,ei=(0,n.css)`
    .leaflet-div-icon {
        background-color: transparent;
        border: none;
    }
`},36357:function(e,t,r){r.r(t),r.d(t,{getPropertyList:()=>a,getPropertyListApi:()=>s,useGetPropertyListQuery:()=>l});var o=r(94362),i=r(20113);let n=o.apiV2ListLink.property.list(o.Scenario.PROPERTY_LIST),s=i.rpApi.injectEndpoints({endpoints:e=>({getPropertyList:e.query({query:e=>({url:n,params:e})})})}),{getPropertyList:a}=s.endpoints,{useGetPropertyListQuery:l}=s},45706:function(e,t,r){r.r(t),r.d(t,{TravelMode:()=>n,formatDuration:()=>s,getTravelModeWithDistanceTime:()=>a});var o,i=r(25433),n=((o={}).DRIVING="DRIVING",o.WALKING="WALKING",o.TRANSIT="TRANSIT",o);let s=(e,t="min")=>{let{days:r,hours:o,minutes:n}=(0,i.intervalToDuration)({start:0,end:1e3*e}),s=r&&24*r,a=s&&!o?`${s} h`:s&&o?`${s+o} h`:o?`${o} h`:"",l=n?`${n} ${t}`:"";return`${a} ${l}`.trim()},a=(e,t)=>{switch(e){case"TRANSIT":return`komunikacj\u{105} miejsk\u{105} ${s(t)}`;case"DRIVING":return`samochodem ${s(t)}`;case"WALKING":return`pieszo ${s(t)}`;default:throw Error("Unknown travel mode")}}},5483:function(e,t,r){r.r(t),r.d(t,{LikeIcon:()=>n});var o=r(52903);r(2784);var i=r(20016);let n=e=>{var t,r;return(0,o.jsx)(i.SvgIcon,(t=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},o=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),o.forEach(function(t){var o;o=r[t],t in e?Object.defineProperty(e,t,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[t]=o})}return e}({},e),r=r={children:(0,o.jsx)("path",{fillRule:"evenodd",clipRule:"evenodd",d:"M6.333 2.33v1.337H9V4.2H5.8V2.055a.533.533 0 0 0-.534-.533v1.066l-.038.088-.184.424L4.222 5h-.555v2.933h4.8V7.4h-1.29v-.533h1.29v-.534h-1.29V5.8h1.29v-.533h-1.29v-.534h1.29V4.2H9v4.267H1V4.2h2.673v.267h.2l.859-1.989V1.163c.16-.101.345-.157.534-.163H5.3a1.064 1.064 0 0 1 1.033 1.33Zm-4.8 5.603h1.6v-3.2h-1.6v3.2Z","data-testid":"thumb-up"})},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);r.push.apply(r,o)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t))}}}]);
//# sourceMappingURL=272.21021a92cba0e886.js.map