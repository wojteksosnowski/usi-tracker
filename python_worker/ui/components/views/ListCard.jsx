(function() {
  const { React, usiRegister, StandardCard, SourceBadge, CategoryStripe, Icon, avgRating } = window;

  /**
   * ListCard - Shared component for Investment lists (Main List & Discovery)
   */
  const ListCardComponent = ({ inv, onSelect, footerRight: CustomFooterRight }) => {
    const safeInv = inv || {};
    const avg = avgRating ? avgRating(safeInv) : 0;
    const thumb = (safeInv.photos && safeInv.photos.length > 0) ? safeInv.photos[0] : (safeInv.image || null);
    const delivery = (safeInv.specifications && (safeInv.specifications.delivery_date || safeInv.specifications.delivery_quarter || safeInv.specifications.delivery_year)) || safeInv.delivery || '—';

    // Default footer right is the star rating
    const DefaultFooterRight = (
      <div className="list-card-avg-box">
        <Icon name="star" size={12} />
        <span className="usi-mono usi-weight-600">{avg.toFixed(2)}</span>
      </div>
    );

    return (
      <StandardCard
        data-component="ListCard"
        image={thumb}
        title={safeInv.name}
        subtitle={safeInv.developer}
        extra={safeInv.district}
        onClick={onSelect}
        badges={
          <div className="usi-flex-row usi-gap-8">
            <SourceBadge source={safeInv.source} />
            {(safeInv.is_new || safeInv.reviewed === false) && <span className="usi-pill success usi-tiny">NOWE</span>}
          </div>
        }
        footerLeft={
          <div className="list-card-footer-left usi-flex-col usi-gap-4">
            <CategoryStripe ratings={safeInv.ratings || {}} />
            <div className="list-card-delivery usi-tiny usi-text-secondary usi-mono usi-flex-row usi-gap-4 usi-align-center" title="Termin oddania">
              <Icon name="calendar" size={11} />
              <span>{delivery}</span>
            </div>
          </div>
        }
        footerRight={CustomFooterRight || DefaultFooterRight}
      />
    );
  };

  const ListCard = React.memo(ListCardComponent, (prev, next) => {
    return prev.inv?.usi_inv_id === next.inv?.usi_inv_id && 
           prev.inv?.updated_at === next.inv?.updated_at &&
           prev.inv?.delivery === next.inv?.delivery &&
           prev.onSelect === next.onSelect;
  });

  usiRegister('ListCard', ListCard);
})();
