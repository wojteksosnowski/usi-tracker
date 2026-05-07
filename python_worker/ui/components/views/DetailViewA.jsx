// DetailViewA.jsx — widok szczegółowy tryb A

(function() {
  const { React, usiRegister, MetadataPanel, RatingsPanel, ModuleWrapper, NearbyInvestmentsModule, ModuleTypes, Gallery, Lightbox } = window;

  const DetailsA = ({ inv, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange, metaConfig }) => {
    const { useDataBus } = window;
    const [marked, setMarked] = React.useState(new Set());
    const [lightbox, setLightbox] = React.useState(null);
    const { bus } = useDataBus();
    
    return (
      <div data-component="DetailsA" className="detail-grid">
        <div className="detail-gallery-column usi-scroll">
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
           <div className="usi-h-24" />
           <MetadataPanel inv={inv} config={metaConfig} />
        </div>

        <div className="detail-ratings-column usi-scroll usi-p-16">
           <RatingsPanel 
              inv={inv} ratings={ratings} handleRating={handleRating} 
              comment={comment} handleComment={handleComment}
              status={status} handleStatus={handleStatus}
              saved={saved} focusedCat={focusedCat}
              onFocusedCatChange={onFocusedCatChange}
           />
        </div>

        <div className="detail-meta-column usi-scroll usi-p-16">
           <ModuleWrapper 
              component={NearbyInvestmentsModule}
              moduleSpec={{
                inputs: { items: { type: ModuleTypes.RecordSet, from: 'nearbyInvestments' } }
              }}
              context={bus}
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
