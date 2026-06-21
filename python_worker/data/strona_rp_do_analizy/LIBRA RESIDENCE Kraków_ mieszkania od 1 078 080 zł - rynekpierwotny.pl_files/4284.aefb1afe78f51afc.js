"use strict";(self.webpackChunkrp=self.webpackChunkrp||[]).push([["4284"],{66103:function(e,r,t){t.r(r),t.d(r,{RelatedArticlesSection:()=>c});var o=t(52903);t(2784);var n=t(98986),s=t(55851),i=t(39725),l=t(86330),a=t(31285);let c=e=>{let{heading:r,articles:t,className:s,as:c="h3"}=e;return(0,o.jsx)("div",{className:(0,n.cx)(u,s),children:(0,o.jsxs)(i.WideContent,{children:[(0,o.jsx)(l.Text,{as:c,className:f,variant:"headline_4",children:r}),(0,o.jsx)(a.HorizontalArticleList,{articles:t})]})})},u=(0,s.css)({backgroundColor:"var(--colors-background-200)",width:"100%",pb:"3.6rem",pt:2,md:{pb:"5.6rem",pt:"3.6rem"}}),f=(0,s.css)({pb:2,md:{pb:"3.6rem"}})},73195:function(e,r,t){t.r(r),t.d(r,{useOnScreenObserver:()=>n});var o=t(2784);let n=(e,r)=>{let[t,n]=(0,o.useState)(!1),s=(0,o.useRef)(null),i=(0,o.useRef)(null),l=r||{threshold:1};return(0,o.useEffect)(()=>("undefined"!=typeof document&&(i.current=document.querySelector(`#${e}`)),s.current=new IntersectionObserver(([e])=>{n(e.isIntersecting)},l),()=>{var e;null==(e=s.current)||e.disconnect()}),[]),{isOnScreen:t,startObserver:()=>{if(i.current){var r;null==(r=s.current)||r.observe(i.current)}else console.error(`Element ${e} does not exist`)},stopObserver:()=>{var e;null==(e=s.current)||e.disconnect()}}}},45515:function(e,r,t){t.r(r),t.d(r,{FavouritesInfoModal:()=>F});var o=t(52903),n=t(2784),s=t(95397),i=t(28165),l=t(7184),a=t(60737),c=t(89143),u=t(89289),f=t(39754),d=t(6511),p=t(83397),m=t(95420),y=t(38633),g=t(6291),b=t(75529),h=t(19743),O=t(70278),v=t(15260),_=t(98519),S=t(4609),j=t(580),x=t(49111),k=t(86330),w=t(6288),L=t(62363),I=t(14273),P=t(52098),E=t(67664);let A=e=>{let{countedFavourites:r}=e,t=(0,I.useResponsiveLinkTarget)(),n=(0,E.getFullKMLink)(w.kmAppLink.site.offers.favouritesWithParams);return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsxs)("div",{css:$,children:[(0,o.jsx)(b.HeartIcon,{size:"2.5",wrapperColor:"#fff",wrapperSize:"2.5"}),(0,o.jsx)(k.Text,{as:"span",variant:"body_copy_2",css:[(0,f.p)(0,0,0,.5)],children:"Zobacz ulubione oferty"})]}),(0,o.jsxs)(k.Text,{as:"div",variant:"info_txt_1",css:T,children:["Posiadasz"," ",(0,o.jsxs)("b",{children:[r," ",L.propertyOffer.accusative(r)]})," ","na liście ulubionych. Skorzystaj z poniższego przycisku, aby je przejrzeć i por\xf3wnać."]}),(0,o.jsx)(j.Button,{href:n,target:t,variant:"filled_primary",size:"small",css:C,onClick:()=>{(0,P.hitGoogleTagManager)({event:"favourite_events",action:"list",label:"list_view"})},children:"Zobacz oferty"})]})},$=(0,i.css)`
    ${(0,x.mb)(2)}
    ${p.flexAlignCenter}
`,T=e=>(0,i.css)`
    ${(0,x.mb)(2)}
    position: relative;
    background-color: #fff;

    @media (max-width: ${e.breakpoints.md}) and (max-height: ${e.breakpoints.sm}) {
        max-height: 21rem;
    }
`,C=(0,i.css)`
    width: 180px;
    max-width: 100%;
`,F=()=>{var e;let r=v.sessionCache.get(_.IS_FAVOURITES_MODAL_CLOSED),{isMobile:t}=(0,O.useUserDevice)(),[i,l]=(0,n.useState)(!1),[f,d]=(0,n.useState)(!!a.get(_.IS_COOKIE_MESSAGE_READ_LS_KEY)),p=(0,h.useIsMounted)(),{favouritePropertiesIds:m,favouriteOfferIds:y,loaded:j}=(0,S.useFavourites)(),x=(0,s.useSelector)(e=>e.subscribedRealEstates.isModalOpen),k=null!=(e=(0,s.useSelector)(e=>e.ui.bottomFixedElementHeight))?e:0,w=Array.from(new Set(m)),L=Array.from(new Set(y)),I=w.length>0?w.length:w.length+L.length;return((0,n.useEffect)(()=>{if(p&&I>0){let e=setInterval(()=>{d(!!a.get(_.IS_COOKIE_MESSAGE_READ_LS_KEY)),a.get(_.IS_COOKIE_MESSAGE_READ_LS_KEY)&&clearInterval(e)},500)}r||t||!x||l(!0)},[p,I]),(p||j)&&0!==I)?i?(0,o.jsxs)(R,{bottomOffset:k,cookiesRead:f,children:[(0,o.jsx)("span",{onClick:()=>{l(!1),v.sessionCache.set(_.IS_FAVOURITES_MODAL_CLOSED,!0)},css:z,children:(0,o.jsx)(g.CloseIcon,{size:"2"})}),(0,o.jsx)(A,{countedFavourites:I})]}):(0,o.jsxs)("div",{css:D(f,k),onClick:()=>{l(!0)},children:[I>0&&(0,o.jsx)("span",{css:M,children:I}),(0,o.jsx)(b.HeartIcon,{size:"2.5",css:[u.pointer,(0,c.elevation)(2)],wrapperColor:"white",wrapperSize:"4",wrapperType:"circle"})]}):null},R=l.default.div`
    ${(0,c.elevation)(3)}
    ${(0,f.p)(2)}
    ${(0,d.borderRadius)(2)}
    position: fixed;
    right: 1.6rem;
    bottom: ${e=>e.cookiesRead?`calc(${e.bottomOffset}px + 1.6rem)`:`${(0,y.calculateRemSize)(16)}`};
    width: 258px;
    z-index: 15; // must be bigger than navigation z-index
    background-color: #fff;

    @media (min-width: ${e=>e.theme.breakpoints.md}) {
        bottom: ${e=>e.cookiesRead?"2.4rem":"8.5rem"};
        right: 3.2rem;
        width: 280px;
    }
`,z=(0,i.css)`
    position: absolute;
    top: 1rem;
    right: 1.6rem;
    cursor: pointer;
`,D=(e,r)=>()=>(0,i.css)`
    ${p.flexAbsoluteCenter};
    position: fixed;
    right: 1.6rem;
    bottom: ${e?`calc(${r}px + 1.6rem)`:`${(0,y.calculateRemSize)(16)}`};
    z-index: 15; // must be bigger than navigation z-index
    cursor: pointer;
    ${u.pointer}
    ${(0,c.elevation)(2)}
        border-radius: 50%;

    ${(0,m.onDesktop)((0,i.css)`
        bottom: ${e?"2.4rem":"8.5rem"};
        right: 2.4rem;
    `)}
`,M=e=>(0,i.css)`
    position: absolute;
    top: -0.5rem;
    right: -0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: ${e.colors.secondary};
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background-color: ${e.colors.primary};
`},37506:function(e,r,t){t.r(r),t.d(r,{useHitUserSegmentLocationEntryOnce:()=>s});var o=t(2784),n=t(2009);function s(e){let{enabled:r,regions:t}=e,s=(0,o.useRef)(!1);(0,o.useEffect)(()=>{!s.current&&r&&((0,n.hitUserSegmentLocationEntry)(t),s.current=!0)},[r,t])}},99569:function(e,r,t){t.r(r),t.d(r,{NearbyOffersPanel:()=>b});var o=t(52903),n=t(2784),s=t(55851),i=t(19616),l=t(66436),a=t(68890),c=t(38683),u=t(66666),f=t(37250),d=t(8939),p=t(68786),m=t(99378),y=t(455);let g="first-nearby-element",b=e=>{let{offersNearby:r,lastElement:t,modalQuery:s,trackingMeta:b,customGridStyle:v}=e,[_,S]=(0,n.useState)(0),j=(0,p.useAppDispatch)(),x=(0,y.useUserPreferencesFilters)();(0,n.useEffect)(()=>{let e=document.getElementById(g);e&&!_&&S(e.offsetHeight)},[]);let{containerId:k}=(0,m.useGTMEcommerceOfferListViewTracking)({offers:r,listId:b.listId,listName:b.listName,useVisibilityTracking:!0});return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsxs)(a.ColumnList,{className:h,rowClassName:O,id:k,"data-id":k,children:[r.map((e,r)=>(0,o.jsx)(c.ColumnListItem,{id:0===r?g:void 0,"data-testid":i.OFFER_TEST_IDS.OFFER_VIEW.NEARBY_OFFERS_TILE,customGridStyle:v,children:(0,o.jsx)(u.OfferBox,{offer:e,index:r,onShowOfferDetailsBtnClick:()=>{j((0,d.showOfferModal)({modalName:"extraOfferModal",offerId:e.id,offer:e,sourceSection:l.ApplicationSourceSection.MODAL}))},trackingMeta:b})},e.id)),!!t&&(0,o.jsx)(c.ColumnListItem,{style:{minHeight:_},customGridStyle:v,children:t},"last")]}),(0,o.jsx)(f.OfferModal,{modalName:"extraOfferModal",offersQuery:s,userPreferencePropertyFilters:x})]})},h=(0,s.css)({paddingLeft:0,paddingRight:0}),O=(0,s.css)({lg:{maxWidth:"100%"}})},20358:function(e,r,t){t.r(r),t.d(r,{NearbyOffersPanelPlaceholder:()=>a});var o=t(52903);t(2784);var n=t(39725),s=t(69822),i=t(38683),l=t(43972);let a=()=>(0,o.jsx)(n.WideContent,{children:(0,o.jsx)(s.Row,{children:[void 0,void 0,void 0].map((e,r)=>(0,o.jsx)(i.ColumnListItem,{children:(0,o.jsx)(l.OfferBoxPlaceholder,{},r)},r))})})},10467:function(e,r,t){t.r(r),t.d(r,{OfferAndPropertyBreadcrumbs:()=>E});var o=t(52903),n=t(2784),s=t(7267),i=t(28165),l=t(68419),a=t(93481),c=t(39540),u=t(49048),f=t(3063),d=t(65306),p=t(67734),m=t(97057),y=t(76755),g=t(15504),b=t(87664),h=t(24252),O=t(89365),v=t(70357),_=t(75349),S=t(50681),j=t(67823),x=t(25128),k=t(54894),w=t(12317),L=t(40284),I=t(72420);function P(e){for(var r=1;r<arguments.length;r++){var t=null!=arguments[r]?arguments[r]:{},o=Object.keys(t);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(t).filter(function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),o.forEach(function(r){var o;o=t[r],r in e?Object.defineProperty(e,r,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[r]=o})}return e}let E=n.memo(e=>{var r;let t=(0,s.useParams)(),n=(0,g.useUserPreferencesQueryParams)(),{type:i,breadcrumbs:c,groups:u,property:h,offer:v,vendor:_,specialListing:S}=e,k=null!=i?(0,j.getOfferTypeNamePluralCapital)(i):"Oferty",w=(0,a.omit)(n,(0,b.getUserPreferencesToOmit)(i)),{region_type_voivodeship:L,region_type_city:I,region_type_county:E,region_type_district:M,region_type_housing_estate:N,region_type_town:U}=c,H=[L,E,I,M,N,U],B=(0,x.getCountryId)(e.country),G=B===y.Country.SPAIN&&(null==(r=H[0])?void 0:r.id)!==null,V=!e.country||B===y.Country.POLAND||G?[{name:k,url:(0,O.buildFriendlyOfferListLink)(P({type:i},w)),key:"offer-type"},...G?T(i,B,w):[],...$(H,i,B,w),...R(c,i,S,H.length,w),...z(_),...C(_,v,u),...F(_,v,h),...D(t)]:[...(e=>{let r={key:"pod-inwestycje",name:"Pod inwestycje",url:f.rpAppLink.investmentOffer.landingPage()},t=m.abroadInvestmentOfferType,o=m.investmentOfferCountries.find(r=>r.country===e);return(0,p.compact)([r,t?{key:t.namePlural,name:t.namePlural,url:f.rpAppLink.investmentOffer.investmentCategory.base({category:t.slug})}:null,t&&o?{key:o.name,name:o.name,url:f.rpAppLink.investmentOffer.investmentCategory.subcategory.base({category:t.slug,subcategory:o.slug})}:null])})(B),...C(_,v,u),...F(_,v,h)];return(0,o.jsx)(d.Breadcrumbs,{homePageUrl:f.rpAppLink.base(),homePageIcon:(0,o.jsx)(l.HomeIcon,{size:"1.4",css:A}),items:V})}),A=(0,i.css)`
    margin: 0 0.4rem 0 0.2rem;
`,$=(e,r,t,o)=>e.reduce((e,n,s)=>{if(null===n)return e;let i=t!==y.Country.POLAND?(()=>{let{friendlySlug:e,countrySlug:s}=(0,_.offerUrlBuilder)({type:r,region:n.slug,country:t}),i=f.rpAppLink.offer.listFriendlyAbroad({friendlySlug:e,abroadRegionSlug:n.slug,country:s});return o?(0,u.appendQueryString)(i,o):i})():(0,O.buildFriendlyOfferListLink)(P({type:r,region:n.slug},o));return[...e,{key:s.toString(),name:n.name,url:i}]},[]),T=(e,r,t)=>{let o=(0,_.offerUrlBuilder)({type:e,region:""}).friendlySlug,n=(0,x.getCountryName)(r),s=f.rpAppLink.offer.listFriendlyAbroad({friendlySlug:o,country:n}),i=t?(0,u.appendQueryString)(s,t):s;return[{key:n,name:(0,c.upperFirst)(n),url:i}]},C=(e,r,t)=>{var o,n;if(!e||!r)return[];let s=(0,h.createOfferLink)((o=P({},r),n=n={vendor:{slug:e.slug},groups:t||null},Object.getOwnPropertyDescriptors?Object.defineProperties(o,Object.getOwnPropertyDescriptors(n)):(function(e,r){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);t.push.apply(t,o)}return t})(Object(n)).forEach(function(e){Object.defineProperty(o,e,Object.getOwnPropertyDescriptor(n,e))}),o));return[{key:"offer-"+r.name,name:r.name,url:s}]},F=(e,r,t)=>{if(!e||!t||!r)return[];let o=f.rpAppLink.property.detail.base({vendorSlug:e.slug,offerSlug:r.slug,offerId:r.id,propertyId:t.id});return[{key:"property-"+t.number,name:`Mieszkanie: ${t.number}`,url:o}]},R=(e,r,t,o,n)=>{if(!t)return[];let s=t.split("-")[0],i=`${s}-${(e=>{if(!e)return"mieszkania-i-domy";switch(e){case v.OfferType.FLAT:return"mieszkania";case v.OfferType.HOUSE:return"domy";case v.OfferType.COMMERCIAL:return"lokale-uzytkowe"}})(r)}${(e=>{let{region_type_voivodeship:r,region_type_city:t,region_type_county:o,region_type_district:n,region_type_town:s}=e;return(null==n?void 0:n.slug)?`-${n.slug}`:(null==s?void 0:s.slug)?`-${s.slug}`:(null==t?void 0:t.slug)?`-${t.slug}`:(null==o?void 0:o.slug)?`-${null==o?void 0:o.slug}`:(null==r?void 0:r.slug)?`-${r.slug}`:""})(e)}`,l=f.rpAppLink.offer.listFriendly({friendlySlug:i});return[{key:"listing-special"+(o+1),name:s,url:n?(0,u.appendQueryString)(l,n):l}]},z=e=>{if(!e)return[];let r=f.rpAppLink.vendor.detail.base({vendorSlug:e.slug,vendorId:e.id});return[{key:"vendor-"+e.name,name:e.name,url:r}]},D=e=>{let{offerListSubFilter:r}=e;if(r&&(0,L.isOfferListSubTypeValidFloorChoice)(r))return[{key:`sub-filter-${r}`,name:function(e){switch(e){case k.OfferListSubType.FLOOR_GROUND:return"parter";case k.OfferListSubType.FLOOR_GROUND_WITH_GARDEN:return"parter z ogr\xf3dkiem";case k.OfferListSubType.LAST_FLOOR:return"ostatnie piętro";default:throw Error("Invalid floor choice in params (offerListSubFilter)")}}(r)}];if(r&&(0,I.isOfferListSubTypeValidHouseFilter)(r))return[{key:`sub-filter-${r}`,name:(0,w.getHouseFilterMetaText)(r)}];let t=e.friendlySlug?(0,S.offerUrlParser)(e.friendlySlug,null==e?void 0:e.offerListSubFilter):null,o=(null==t?void 0:t.rooms_1)&&t.rooms_1===t.rooms_0,n=!(null==t?void 0:t.rooms_0)&&(null==t?void 0:t.rooms_1)===1,s=(null==t?void 0:t.rooms_1)||(null==t?void 0:t.rooms_0),i=!(null==t?void 0:t.rooms_1)&&(null==t?void 0:t.rooms_0)===5;if((n||o||i)&&s)return[{key:"rooms",name:{1:(null==t?void 0:t.type)===v.OfferType.FLAT?"kawalerki":"jednopokojowe",2:"dwupokojowe",3:"trzypokojowe",4:"czteropokojowe",5:"pięciopokojowe i więcej"}[s]}];let l=null==t?void 0:t.price_0,a=null==t?void 0:t.price_1;if(!l&&a||!a&&l){let e=Math.ceil((a||l)/1e3),r=0,t="tys";return e<1e3?r=e:(r=1e3===e?1:parseFloat((e/1e3).toFixed(3).replace(/\.?0+$/,"")),t="mln"),[{key:"price",name:`${a?"Do":"Od"} ${r} ${t}`}]}return[]}},43972:function(e,r,t){t.r(r),t.d(r,{OfferBoxPlaceholder:()=>i});var o=t(52903);t(2784);var n=t(28165),s=t(76223);let i=()=>(0,o.jsx)(s.OfferBoxBase,{children:(0,o.jsx)("div",{css:f,children:(0,o.jsxs)("div",{css:d,children:[(0,o.jsx)("div",{css:l}),(0,o.jsxs)("div",{css:a,children:[(0,o.jsx)("div",{css:c}),(0,o.jsx)("div",{css:u})]})]})})}),l=e=>(0,n.css)`
    height: 45%;
    background-color: ${e.colors.gray[200]};
    width: 100%;
`,a=(0,n.css)`
    display: flex;
    justify-content: flex-end;
    flex-direction: column;
    flex: 1;
    padding: 0 3rem 3rem;
`,c=e=>(0,n.css)`
    height: 60%;
    background-color: ${e.colors.gray[200]};
    margin-bottom: 1.5rem;
`,u=e=>(0,n.css)`
    bottom: 1.5rem;
    height: 39px;
    background-color: ${e.colors.gray[200]};
`,f=(0,n.css)`
    height: 0;
    overflow: hidden;
    padding-top: 125%;
    background: white;
    position: relative;
`,d=(0,n.css)`
    display: flex;
    flex-direction: column;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
`},9472:function(e,r,t){t.r(r),t.d(r,{neighborhoodOffersViewHit:()=>s,neighborhoodOffersViewHitAlgolytics:()=>i});var o=t(34213),n=t(65006);let s=(e,r)=>{var t,o;i((t=function(e){for(var r=1;r<arguments.length;r++){var t=null!=arguments[r]?arguments[r]:{},o=Object.keys(t);"function"==typeof Object.getOwnPropertySymbols&&(o=o.concat(Object.getOwnPropertySymbols(t).filter(function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),o.forEach(function(r){var o;o=t[r],r in e?Object.defineProperty(e,r,{value:o,enumerable:!0,configurable:!0,writable:!0}):e[r]=o})}return e}({},(0,n.getTrackedSiteData)()),o=o={view_type:e,offers_id:r},Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(o)):(function(e,r){var t=Object.keys(e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);t.push.apply(t,o)}return t})(Object(o)).forEach(function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(o,e))}),t))},i=(0,o.delayHit)(e=>(0,o.hitAlgolytics)("neighborhood_offers_open",e),500)},99378:function(e,r,t){t.r(r),t.d(r,{useGTMEcommerceOfferListViewTracking:()=>i});var o=t(2784),n=t(38374),s=t(51025);let i=e=>{let{useVisibilityTracking:r,isListReady:t=!0}=e,{containerId:i,isWaitingForElement:l}=(0,s.useElementViewportShowingUpStatus)({useVisibilityTracking:r});return(0,o.useEffect)(()=>{!l&&e.offers.length&&t&&(0,n.hitGTMOfferViewItemList)({offers:e.offers,listId:e.listId,listName:e.listName})},[l,t,e.offers,e.listId,e.listName]),{containerId:i}}},15504:function(e,r,t){t.r(r),t.d(r,{useUserPreferencesQueryParams:()=>s});var o=t(2784),n=t(26159);let s=()=>{let{data:e}=(0,n.useGetUserPreferencesQuery)();return(0,o.useMemo)(()=>(e=>{if(!(null==e?void 0:e.filters))return{};let{filters:r}=e,t={};return r.type&&(t.type=parseInt(r.type,10)),r.price_0&&(t.price_0=parseInt(r.price_0,10)),r.price_1&&(t.price_1=parseInt(r.price_1,10)),r.area_0&&(t.area_0=parseInt(r.area_0,10)),r.area_1&&(t.area_1=parseInt(r.area_1,10)),r.rooms_0&&(t.rooms_0=parseInt(r.rooms_0,10)),r.rooms_1&&(t.rooms_1=parseInt(r.rooms_1,10)),r.construction_end_date&&(t.construction_end_date=r.construction_end_date),r.floor_choices&&r.floor_choices.length>0&&(t.floor_choices=r.floor_choices),(null==r?void 0:r.house_storeys)&&r.house_storeys.length>0&&(t.house_storeys=r.house_storeys),t})(e),[e])}},87664:function(e,r,t){t.r(r),t.d(r,{getUserPreferencesToOmit:()=>n});var o=t(70357);let n=e=>{switch(e){case o.OfferType.FLAT:return["house_storeys"];case o.OfferType.HOUSE:return["floor_choices"];case o.OfferType.COMMERCIAL:case o.OfferType.MODULAR_HOUSE:default:return["house_storeys","floor_choices"]}}}}]);
//# sourceMappingURL=4284.aefb1afe78f51afc.js.map