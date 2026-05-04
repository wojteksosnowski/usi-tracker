// Icon.jsx — atomowy komponent ikon

function Icon({ name, size = 16, stroke = 1.6 }) {
  const { React } = window;
  const paths = {
    search: <><circle cx="7" cy="7" r="5"/><path d="M11 11l4 4"/></>,
    filter: <path d="M2 4h12M4 8h8M6 12h4"/>,
    grid: <><rect x="2" y="2" width="5" height="5"/><rect x="9" y="2" width="5" height="5"/><rect x="2" y="9" width="5" height="5"/><rect x="9" y="9" width="5" height="5"/></>,
    list: <><path d="M2 4h12M2 8h12M2 12h12"/></>,
    chevron: <path d="M5 3l4 4-4 4"/>,
    chevronDown: <path d="M3 5l4 4 4-4"/>,
    chevronLeft: <path d="M11 13L5 7l6-6"/>,
    arrow: <><path d="M3 8h10M9 4l4 4-4 4"/></>,
    trash: <><path d="M3 4h10M5 4V2h6v2M4 4l1 10h6l1-10"/></>,
    eye: <><path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z"/><circle cx="8" cy="8" r="2"/></>,
    check: <path d="M3 8l3 3 7-7"/>,
    close: <path d="M3 3l10 10M13 3L3 13"/>,
    star: <path d="M8 2l1.8 4 4.2.4-3.2 2.8 1 4.4L8 11.4 4.2 13.6l1-4.4L2 6.4l4.2-.4z"/>,
    map: <><path d="M2 4l4-2 4 2 4-2v10l-4 2-4-2-4 2z"/><path d="M6 2v10M10 4v10"/></>,
    plus: <path d="M8 3v10M3 8h10"/>,
    sparkle: <><path d="M8 1v3M8 12v3M1 8h3M12 8h3M3 3l2 2M11 11l2 2M3 13l2-2M11 5l2-2"/></>,
    grip: <><circle cx="6" cy="4" r="1"/><circle cx="10" cy="4" r="1"/><circle cx="6" cy="8" r="1"/><circle cx="10" cy="8" r="1"/><circle cx="6" cy="12" r="1"/><circle cx="10" cy="12" r="1"/></>,
    sort: <><path d="M5 3v10M3 11l2 2 2-2"/><path d="M11 13V3M9 5l2-2 2 2"/></>,
    undo: <><path d="M3 7h7a3 3 0 010 6H6"/><path d="M5 4L2 7l3 3"/></>,
    info: <><circle cx="8" cy="8" r="6"/><path d="M8 7v4M8 5h.01"/></>,
    menu: <><path d="M2 4h12M2 8h12M2 12h12"/></>,
    download: <><path d="M8 2v10M4 8l4 4 4-4"/></>,
    building: <path d="M2 14V2h8v12M10 6h4v8M5 5h1M5 8h1M5 11h1" />,
  };
  const path = paths[name] || <circle cx="8" cy="8" r="6" opacity="0.3" />;
  return (
    <svg data-component="Icon" width={size} height={size} viewBox="0 0 16 16" fill="none"
      stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
      {path}
    </svg>
  );
}
window.usiRegister('Icon', Icon);
