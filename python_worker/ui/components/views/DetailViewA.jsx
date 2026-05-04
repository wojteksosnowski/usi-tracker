// DetailViewA.jsx — widok szczegółowy tryb A

(function() {
  const { React, usiRegister, MetadataPanel, RatingsPanel, ModuleWrapper, NearbyInvestmentsModule, ModuleTypes, Gallery, Lightbox } = window;

  const DetailsA = ({ inv, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange, metaConfig, moduleContext }) => {
    const [marked, setMarked] = React.useState(new Set());
    const [lightbox, setLightbox] = React.useState(null);
    
    return (
      <div data-component="DetailsA" style={{ display: 'grid', gridTemplateColumns: '1fr 340px 300px', gap: 24, flex: 1, overflow: 'hidden' }}>
        <div style={{ padding: '0 8px 24px 0', overflow: 'auto' }} className="usi-scroll">
           <Gallery 
              inv={inv} 
              columns={3} 
              marked={marked} 
              onToggleMark={(idx) => {
                  const next = new Set(marked);
                  if (next.has(idx)) next.delete(idx); else next.add(idx);
                  setMarked(next);
              }} 
              onLightbox={setLightbox} 
           />
           <div style={{ height: 24 }} />
           <MetadataPanel inv={inv} config={metaConfig} />
        </div>

        <div style={{ borderLeft: '.5px solid var(--usi-border)', padding: '0 18px', overflow: 'auto' }} className="usi-scroll">
           <RatingsPanel 
              inv={inv} ratings={ratings} handleRating={handleRating} 
              comment={comment} handleComment={handleComment}
              status={status} handleStatus={handleStatus}
              saved={saved} focusedCat={focusedCat}
              onFocusedCatChange={onFocusedCatChange}
           />
        </div>

        <div style={{ borderLeft: '.5px solid var(--usi-border)', padding: '0 0 0 18px', overflow: 'auto' }} className="usi-scroll">
           <ModuleWrapper 
              component={NearbyInvestmentsModule}
              moduleSpec={{
                inputs: { items: { type: ModuleTypes.RecordSet, from: 'nearbyInvestments' } }
              }}
              context={window.useDataBus().bus}
              title="W okolicy"
              icon="map"
              height={400}
           />
        </div>
        {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
      </div>
    );
  };
  usiRegister('DetailsA', DetailsA);
})();
