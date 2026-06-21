"use strict";(self.webpackChunkrp=self.webpackChunkrp||[]).push([["2749"],{38855:function(e,t,r){r.r(t),r.d(t,{ApplicationTermsAcceptation:()=>c});var i=r(52903),o=r(55851),n=r(86330),a=r(3063);let c=e=>{let{color:t="var(--colors-gray-700)",className:r,isPartnerTerms:o,sourceForm:c}=e,s=a.rpAppLink.partnersTerms.base(),p=o?s:a.rpAppLink.termsOfService.base();return(0,i.jsxs)(n.Text,{variant:"info_txt_1",color:t||"var(--colors-gray-700)",className:r,align:"center",children:["Akceptuję"," ",(0,i.jsxs)("a",{href:p,target:"_blank",className:l,children:["regulamin",(null==c?void 0:c.source)!=="applicationSideBar"||(null==c?void 0:c.isUserLogged)?" serwisu.":""]}),(null==c?void 0:c.source)!=="applicationSideBar"||(null==c?void 0:c.isUserLogged)?"":" i zakładam konto w Portalu."]})},l=(0,o.css)({textDecoration:"underline",color:"var(--colors-gray-700)","&, &:link, &:visited, &:hover, &:active":{textDecoration:"underline",color:"var(--colors-gray-700)"}})},90100:function(e,t,r){r.r(t),r.d(t,{gtmFavouriteAddToFavouritesClick:()=>n,gtmFavouritesMultileadAddToFavourites:()=>a,gtmFavouritesMultileadModalOpen:()=>c,gtmFavouritesMultileadSendLead:()=>l});var i=r(52098),o=r(91346);let n=e=>{let t={event:o.FavouritesGTMEvent.FAVOURITE,action:e?o.FavouritesGTMAction.FAVOURITES_ADD_TO_FAVOURITE:o.FavouritesGTMAction.FAVOURITES_DELETE_FROM_FAVOURITE};(0,i.hitGoogleTagManager)(t)},a=()=>{let e={event:o.FavouritesGTMEvent.FAVOURITE,action:o.FavouritesGTMAction.FAVOURITES_MULTILEAD_ADD_TO_FAVOURITE};(0,i.hitGoogleTagManager)(e)},c=()=>{let e={event:o.FavouritesGTMEvent.FAVOURITE,action:o.FavouritesGTMAction.FAVOURITES_MULTILEAD_MODAL_OPEN_BUTTON_CLICK};(0,i.hitGoogleTagManager)(e)},l=()=>{let e={event:o.FavouritesGTMEvent.FAVOURITE,action:o.FavouritesGTMAction.FAVOURITES_MULTILEAD_SEND_LEAD_BUTTON_CLICK};(0,i.hitGoogleTagManager)(e)}},58402:function(e,t,r){r.r(t),r.d(t,{MyFavouritesListNavigationItemValue:()=>o,myFavouritesListNavigationOptions:()=>n});var i,o=((i={})[i.LIST=0]="LIST",i[i.APPLICATIONS=1]="APPLICATIONS",i);let n=[{value:0,label:"Twoja lista"},{value:1,label:"Twoje zapytania"}]},68029:function(e,t,r){r.r(t),r.d(t,{getGTMEcommerceItemStatus:()=>n});var i=r(70638),o=r(31856);let n=e=>!function(e){let t=(0,i.getOfferDisplayStatus)(e);return e.configuration.limited_presentation&&"limited"===t}(e)?o.GTMEcommerceItemStatus.Active:o.GTMEcommerceItemStatus.Archived},65432:function(e,t,r){r.r(t),r.d(t,{getGtmEcommerceOfferAvailability:()=>n});var i=r(29999),o=r(21678);let n=e=>{var t,r;let n=!(null==(t=e.configuration)?void 0:t.display_type)||e.configuration.display_type===i.OfferDisplayType.FOR_SALE,a=!!(null==(r=e.configuration)?void 0:r.limited_presentation);return{availability:n&&!a?o.GTMEcommerceAvailability.IN_STOCK:o.GTMEcommerceAvailability.OUT_OF_STOCK}}},43086:function(e,t,r){r.r(t),r.d(t,{getGTMEcommerceSpainParams:()=>o});var i=r(76755);let o=(e,t)=>e===i.Country.SPAIN?function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}({},(null==t?void 0:t.distance_from_the_airport)?{item_airport_distance:t.distance_from_the_airport.toString()}:{},(null==t?void 0:t.distance_from_the_beach)?{item_beach_distance:t.distance_from_the_beach.toString()}:{}):{}},35299:function(e,t,r){r.r(t),r.d(t,{hitGTMPropertySelectItem:()=>y});var i=r(13784),o=r(52098),n=r(68029),a=r(65432),c=r(62047),l=r(94771),s=r(83225),p=r(43086);function u(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}function f(e,t){return t=null!=t?t:{},Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(t)).forEach(function(r){Object.defineProperty(e,r,Object.getOwnPropertyDescriptor(t,r))}),e}let y=e=>{var t;let r=u(f(u(f(u(f(u({},(0,c.getGtmEcommerceOfferItemBaseProps)(e.offer)),{item_category:"property",price:1,quantity:1}),(0,a.getGtmEcommerceOfferAvailability)(e.offer)),{item_status:(0,n.getGTMEcommerceItemStatus)(e.offer),item_type:i.gtmEcommerceOfferTypeMap[e.offer.type]}),(0,l.getGTMEcommerceOfferRegion)(e.offer.region),(0,p.getGTMEcommerceSpainParams)(null==(t=e.offer.region)?void 0:t.country,e.offer)),{item_comissioning_date:e.offer.construction_date_range.upper||"na",item_list_name:e.listName,item_list_id:e.listId}),(0,s.getGTMEcommercePropertyProps)({property:e.property,short:!1})),y={item_list_id:e.listId,item_list_name:e.listName,items:[r]};(0,o.hitGoogleTagManager)({event:"select_item",ecommerce:y})}},11811:function(e,t,r){r.r(t),r.d(t,{hitGTMPropertyViewItemList:()=>l});var i=r(52098),o=r(62047),n=r(83225);function a(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}function c(e,t){return t=null!=t?t:{},Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(t)).forEach(function(r){Object.defineProperty(e,r,Object.getOwnPropertyDescriptor(t,r))}),e}let l=e=>{var t,r;let l=(((null==(t=e.listParams)?void 0:t.page)||1)-1)*((null==(r=e.listParams)?void 0:r.pageSize)||10),p=e.properties.map((t,r)=>c(a(c(a({},(0,o.getGtmEcommerceOfferItemBaseProps)(s(e)?e.offer:t.offer)),{item_category:"property"}),(0,n.getGTMEcommercePropertyProps)({property:t,short:!0})),{index:r+1+(l||0)}));(0,i.hitGoogleTagManager)({event:"view_item_list",ecommerce:{item_list_id:e.listId,item_list_name:e.listName,items:p}})},s=e=>!!("offer"in e&&e.offer)},29071:function(e,t,r){r.r(t),r.d(t,{FavouritesListCollectionName:()=>y,FavouritesListConfirmationButton:()=>O,FavouritesListEventTypes:()=>m,handleComparisonModalButtonClickHit:()=>v,handleComparisonModalRenderHit:()=>h,handleFavouritesListApplicationOpenHit:()=>b,handleFavouritesListCheckHit:()=>g,handleFavouritesListNavigationClickHit:()=>w,handleFavouritesListRenderHit:()=>d,handleFavouritesMultiApplicationHit:()=>j,handleGoToAppliedModalButtonClickHit:()=>_});var i,o,n,a=r(34213),c=r(66436),l=r(58402),s=r(74816),p=r(65006);function u(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}function f(e,t){return t=null!=t?t:{},Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(t)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(t)).forEach(function(r){Object.defineProperty(e,r,Object.getOwnPropertyDescriptor(t,r))}),e}var y=((i={}).MY_LIST_COLLECTION="my_list",i.MY_LIST_OPEN="my_list_open",i.MY_LIST_BUTTONS="my_list_buttons",i.MY_LIST_CHECKED="my_list_checked",i.APPLICATION_OPEN="application_open",i.COMPARISON_TOOL="comparison",i.FAVOURITES_MULTILEAD="favourites_lead_for_all_send",i),m=((o={}).FAVOURITES_LIST_MY_LIST_CLICK="show_my_list",o.FAVOURITES_LIST_APPLIED_LIST_CLICK="show_my_application",o.FAVOURITES_LIST_RENDER="my_list_open",o.FAVOURITES_LIST_INTERACTION="my_list_interaction",o.FAVOURITES_LIST_APPLICATIONS_BUTTON="my_applications_button_click",o.FAVOURITES_LIST_COMPARISON_TOOL_BUTTON="comparison_button_click",o.POPUP_DISPLAY="popup_display",o),O=((n={}).APPLIED_LIST="applied_list",n.COMPARISON_TOOL="comparison_tool",n);let d=(e,t)=>{let r=f(u({},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST,event_type:"my_list_open",offers:e,properties:t});(0,a.hitAlgolytics)("my_list_open",r)},b=e=>{let t=e?c.ApplicationSource.FavouritesOfferInquiry:c.ApplicationSource.FavouritesPropertyInquiry,r=f(u({},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST,source:(0,c.getApplicationSourceDisplay)(t),source_id:t,source_section:c.ApplicationSourceSection.FAVOURITES});(0,a.hitAlgolytics)("application_open",r)},g=(e,t,r)=>{let i=f(u({},(0,p.getTrackedSiteData)()),{event_type:"my_list_interaction",offer_id:t,property_id:r||null,checked:e});(0,a.hitAlgolytics)("my_list_checked",i)},h=()=>{let e=f(u({},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST,event_type:"popup_display"});(0,a.hitAlgolytics)("comparison",e)},_=()=>{let e=f(u({event_type:"my_applications_button_click"},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST});(0,a.hitAlgolytics)("my_list_buttons",e)},v=()=>{let e=f(u({},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST,event_type:"comparison_button_click"});(0,a.hitAlgolytics)("comparison",e)},w=e=>{let t={};t=f(u({},t=e===l.MyFavouritesListNavigationItemValue.LIST?{event_type:"show_my_list"}:{event_type:"show_my_application"},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST}),(0,a.hitAlgolytics)("my_list_buttons",t)},j=e=>{let t=f(u({},(0,p.getTrackedSiteData)()),{view_type:s.ViewType.MY_FAVOURITES_LIST,data:e});(0,a.hitAlgolytics)("favourites_lead_for_all_send",t)}},30266:function(e,t,r){r.r(t),r.d(t,{getAmplitudeViewItemEventProperties:()=>c});var i=r(13784),o=r(94771),n=r(48624);function a(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}let c=e=>{let{offer:t,property:r,itemListId:c,itemListName:l}=e,s=a({item_id:t.id,item_name:t.name,item_brand:t.vendor.name,item_category:r?"property":"investment",item_type:i.gtmEcommerceOfferTypeMap[t.type],currency:(0,n.getCurrencyISOCode)(t.currency)},(e=>{let t=(0,o.getGTMEcommerceOfferRegion)(e);return a({},t.item_category2?{item_category2:t.item_category2}:{},t.item_category3?{item_category3:t.item_category3}:{},t.item_category4?{item_category4:t.item_category4}:{},t.item_category5?{item_category5:t.item_category5}:{})})(t.region));return c&&(s.item_list_id=c),l&&(s.item_list_name=l),r&&(s.property_id=r.id,s.variant_name=r.number,null!=r.area&&(s.variant_area=r.area),null!=r.rooms&&(s.variant_rooms=r.rooms),null!=r.floor&&(s.variant_floor=r.floor),null!=r.price&&(s.price=r.price)),s}},90447:function(e,t,r){r.r(t),r.d(t,{trackAmplitudePropertySelectItem:()=>n});var i=r(79075),o=r(30266);let n=e=>{(0,i.trackAmplitudeEvent)("select_item",(({offer:e,property:t,index:r,itemListId:i,itemListName:n})=>{var a,c;return a=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}({},(0,o.getAmplitudeViewItemEventProperties)({offer:e,property:t,itemListId:i,itemListName:n}),null!=t.price?{item_price:t.price}:{}),c=c={index:r},Object.getOwnPropertyDescriptors?Object.defineProperties(a,Object.getOwnPropertyDescriptors(c)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(c)).forEach(function(e){Object.defineProperty(a,e,Object.getOwnPropertyDescriptor(c,e))}),a})(e))}},51025:function(e,t,r){r.r(t),r.d(t,{useElementViewportShowingUpStatus:()=>n});var i=r(2784),o=r(84055);let n=({useVisibilityTracking:e})=>{let t=(0,i.useId)(),[r,n]=(0,i.useState)(e);return(0,o.useElementWasVisible)({ids:[t],onElementVisible:()=>{n(!1)},once:!0,threshold:.05,disabled:!e}),{containerId:t,isWaitingForElement:e&&r}}},84055:function(e,t,r){r.r(t),r.d(t,{useElementWasVisible:()=>o});var i=r(2784);let o=e=>{let t=(0,i.useRef)([]);(0,i.useEffect)(()=>{if(e.disabled||!("IntersectionObserver"in window))return;let r=new IntersectionObserver(r=>{r.forEach(r=>{let i=r.target.getAttribute("data-id");if(r.isIntersecting)if(e.once){!t.current.includes(i)&&(t.current=t.current.concat(i),e.onElementVisible(i,r),Number(i)&&e.indexes&&e.onElementVisible(i,r,e.indexes[i]));return}else e.onElementVisible(i,r)})},{threshold:[e.threshold?e.threshold:1]}),i=[];return e.ids.forEach(e=>{let t=document.querySelector(`[data-id="${e}"]`);t&&(r.observe(t),i.push(t))}),()=>{i.forEach(e=>r.unobserve(e))}},[JSON.stringify(e.ids),e.disabled])}},17866:function(e,t,r){r.r(t),r.d(t,{CenteredImage:()=>j});var i=r(52903),o=r(2784),n=r(28165),a=r(7184),c=r(78671);let l=e=>{var t,r;return(0,i.jsxs)(c.SvgIcon,(t=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}({},e),r=r={children:[(0,i.jsx)("path",{d:"M5.00003 6.59019C5.86635 6.59019 6.56865 5.8856 6.56865 5.01643C6.56865 4.14725 5.86635 3.44266 5.00003 3.44266C4.13369 3.44266 3.4314 4.14725 3.4314 5.01643C3.4314 5.8856 4.13369 6.59019 5.00003 6.59019Z"}),(0,i.jsx)("path",{d:"M3.52938 0.0983276L2.63232 1.08193H1.07841C0.539191 1.08193 0.0980148 1.52456 0.0980148 2.06554V7.96717C0.0980148 8.50816 0.539191 8.95079 1.07841 8.95079H8.92154C9.46076 8.95079 9.90194 8.50816 9.90194 7.96717V2.06554C9.90194 1.52456 9.46076 1.08193 8.92154 1.08193H7.36762L6.47056 0.0983276H3.52938ZM4.99997 7.47538C3.64703 7.47538 2.549 6.37373 2.549 5.01636C2.549 3.65898 3.64703 2.55735 4.99997 2.55735C6.35291 2.55735 7.45096 3.65898 7.45096 5.01636C7.45096 6.37373 6.35291 7.47538 4.99997 7.47538Z"})]},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t))},s=()=>(0,i.jsx)("div",{css:p,children:(0,i.jsx)(l,{css:u})}),p=e=>(0,n.css)`
    background-color: ${e.colors.gray[300]};
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
`,u=e=>(0,n.css)`
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(6);
    fill: ${e.colors.gray[700]};
    max-width: 100%;
`,f=(0,o.forwardRef)((e,t)=>{var r,n,a;let{src:c,src2x:l,src3x:p,alt:u,ratio:f,loading:O,width:d,height:b,className:g,imageClassName:h,imageCss:_,fetchPriority:v,imageStyle:w}=e,[j,S]=(0,o.useState)(!1),P=(r=c,n=l,a=p,n&&a?`${r}, ${n} 2x, ${a} 3x`:n?`${r}, ${n} 2x`:r);return(0,o.useEffect)(()=>{S(!1)},[c]),(0,i.jsx)(y,{className:g,ratio:f,hasError:j,onClick:e.onClick,children:j||!c?(0,i.jsx)(s,{}):(0,i.jsx)("img",{ref:t,src:c,srcSet:P,style:w,alt:u,onError:()=>{var t;S(!0),null==(t=e.onError)||t.call(e)},loading:O,width:d,height:b,className:h,css:[_,m(f)],fetchPriority:v})})}),y=a.default.div`
    position: relative;
    line-height: 0;
    display: inline-block;
    overflow: hidden; // For cases when we want to style border radius while using aspect ratio

    // When no ratio is provided height and width needs to be provided in case we use fallback
    ${e=>e.hasError&&!e.ratio&&(0,n.css)`
            height: ${e.height};
            width: ${e.width};
            max-width: 100%;
        `}

    // Calculate and use Aspect Ratio Boxes
    ${e=>e.ratio&&(0,n.css)`
            display: block;
            &:before {
                content: "";
                display: block;

                ${e.ratio&&O(...d(e.ratio.xs))};

                @media screen and (min-width: ${e.theme.breakpoints.xs}) {
                    ${e.ratio&&e.ratio.md&&O(...d(e.ratio.md))}
                }
            }
        `}
`,m=e=>(0,n.css)`
    ${e&&(0,n.css)`
        position: absolute;
        left: 0;
        top: 0;
        display: block;
        max-width: 100%;
        height: auto;
    `}
`,O=(e,t)=>(0,n.css)`
    padding-top: ${t/e*100+"%"};
`,d=e=>{let[t,r]=e.split(":").map(e=>parseInt(e));return[t,r]},b=(0,o.forwardRef)((e,t)=>{var r,o;let{fit:a,hasError:c,alt:l,fetchPriority:s,onLoad:p}=e,u=function(e,t){if(null==e)return{};var r,i,o=function(e,t){if(null==e)return{};var r,i,o={},n=Object.keys(e);for(i=0;i<n.length;i++)r=n[i],t.indexOf(r)>=0||(o[r]=e[r]);return o}(e,t);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);for(i=0;i<n.length;i++)r=n[i],!(t.indexOf(r)>=0)&&Object.prototype.propertyIsEnumerable.call(e,r)&&(o[r]=e[r])}return o}(e,["fit","hasError","alt","fetchPriority","onLoad"]);return(0,i.jsx)("img",(r=function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}({ref:t,alt:l},u),o=o={fetchPriority:s,onLoad:p,css:(({hasError:e,fit:t})=>(0,n.css)`
    display: block;
    max-width: 100%;
    width: auto;
    height: auto;

    ${e?"display: none;":""}

    ${t&&(0,n.css)`
        object-fit: cover;
        object-position: ${t};
        height: 100%;
        width: 100%;
    `}
`)({hasError:c,fit:a})},Object.getOwnPropertyDescriptors?Object.defineProperties(r,Object.getOwnPropertyDescriptors(o)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(o)).forEach(function(e){Object.defineProperty(r,e,Object.getOwnPropertyDescriptor(o,e))}),r))}),g=e=>{let[t,r]=(0,o.useState)(!1),n=(0,o.useRef)(null),{sources:a,className:c,fit:l,fetchPriority:p}=e,u=a.sort((e,t)=>t.minWidthPX-e.minWidthPX),f=u[u.length-1];return(0,i.jsx)(_,{className:c,onError:()=>r(!0),hasError:t,containerSizes:a,fit:l,children:(0,i.jsxs)(i.Fragment,{children:[(t||0===e.sources.length)&&(0,i.jsx)(s,{}),u.map(e=>{var{minWidthPX:t,width:r,height:o}=e,n=function(e,t){if(null==e)return{};var r,i,o=function(e,t){if(null==e)return{};var r,i,o={},n=Object.keys(e);for(i=0;i<n.length;i++)r=n[i],t.indexOf(r)>=0||(o[r]=e[r]);return o}(e,t);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);for(i=0;i<n.length;i++)r=n[i],!(t.indexOf(r)>=0)&&Object.prototype.propertyIsEnumerable.call(e,r)&&(o[r]=e[r])}return o}(e,["minWidthPX","width","height"]);let a="srcSet"in n?n.srcSet:n.src;return(0,i.jsx)("source",{media:`(min-width: ${t}px)`,width:r,height:o,srcSet:a},t)}),(0,i.jsx)(b,function(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}({alt:e.alt,loading:e.loading,height:f.height,width:f.width,fit:l,ref:n,hasError:t,fetchPriority:p,onLoad:e=>{e.currentTarget.complete&&0===e.currentTarget.naturalWidth&&r(!0),e.currentTarget.complete&&0!==e.currentTarget.naturalWidth&&r(!1)}},h(f)))]})})},h=e=>"srcSet"in e?{srcSet:e.srcSet}:{src:e.src},_=a.default.picture`
    display: block;
    ${e=>e.fit&&(0,n.css)`
            height: 100%;
        `}

    ${e=>e.hasError&&(0,n.css)`
            position: relative;
            width: 100%;

            &:before {
                content: "";
                display: block;
            }

            ${e.containerSizes.sort((e,t)=>e.minWidthPX-t.minWidthPX).map(e=>(0,n.css)`
                        @media screen and (min-width: ${e.minWidthPX+"px"}) {
                            max-width: ${e.width+"px"};

                            &:before {
                                ${v(e.height,e.width)}
                            }
                        }
                    `)}
        `}
`,v=(e,t)=>(0,n.css)`
    padding-top: ${e/t*100+"%"};
`;function w(e){for(var t=1;t<arguments.length;t++){var r=null!=arguments[t]?arguments[t]:{},i=Object.keys(r);"function"==typeof Object.getOwnPropertySymbols&&(i=i.concat(Object.getOwnPropertySymbols(r).filter(function(e){return Object.getOwnPropertyDescriptor(r,e).enumerable}))),i.forEach(function(t){var i;i=r[t],t in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i})}return e}function j(e){var t,r;let{breakpoints:o,className:n,sources:a,customComponents:c,maxSourceWidth:l}=e,s=function(e,t){if(null==e)return{};var r,i,o=function(e,t){if(null==e)return{};var r,i,o={},n=Object.keys(e);for(i=0;i<n.length;i++)r=n[i],t.indexOf(r)>=0||(o[r]=e[r]);return o}(e,t);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);for(i=0;i<n.length;i++)r=n[i],!(t.indexOf(r)>=0)&&Object.prototype.propertyIsEnumerable.call(e,r)&&(o[r]=e[r])}return o}(e,["breakpoints","className","sources","customComponents","maxSourceWidth"]);return(0,i.jsx)(S,{breakpoints:o,css:[T,E(l)],className:n,initialHeight:s.height,children:a?(0,i.jsx)(g,w({sources:a},s)):c&&c.Image?(0,i.jsx)(c.Image,w({},s)):(0,i.jsx)(f,(t=w({},s),r=r={width:`${s.width}px`,height:`${s.height}px`},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(r)):(function(e,t){var r=Object.keys(e);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);r.push.apply(r,i)}return r})(Object(r)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(r,e))}),t))})}let S=a.default.div`
    max-height: 100%;
    max-width: 100%;

    img {
        height: 100%;
        width: auto;
        max-width: unset;
    }

    ${({breakpoints:e,initialHeight:t})=>(0,n.css)`
        display: flex;
        position: relative;
        overflow: hidden;

        ${!e&&(0,n.css)`
            height: ${t}px;
        `};

        ${e&&(0,n.css)`
            ${P(e)}
        `};
    `}
`,P=e=>e.map(e=>(0,n.css)`
            @media (min-width: ${e.mediaWidth}) {
                width: ${e.width};
                height: ${e.height};
            }
        `),T=(0,n.css)`
    flex: 1;
`,E=e=>(0,n.css)`
    & > * {
        height: 100%;
        width: 100%;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    & > * img {
        height: 100%;
        width: auto;
        position: absolute;
    }

    ${e&&(0,n.css)`
        & > * img {
            @media screen and (min-width: ${e}px) {
                height: auto !important;
                width: 100% !important;
            }
        }
    `}
`},7551:function(e,t,r){r.r(t),r.d(t,{listUnStyled:()=>o});var i=r(28165);let o=(0,i.css)`
    padding-left: 0;
    list-style: none;
    //  TODO: Shouldn't we remove also the margin?
`}}]);
//# sourceMappingURL=2749.33e3bafbd896471f.js.map