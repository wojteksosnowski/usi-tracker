(function() {
  const { React, usiRegister, StandardCard, SourceBadge, CategoryStripe, Icon, avgRating } = window;

  /**
   * ListCard - Shared component for Investment lists (Main List & Discovery)
   */
  const ListCardComponent = ({ inv, onSelect, footerRight: CustomFooterRight }) => {
    const avg = avgRating ? avgRating(inv) : 0;
    const thumb = (inv.photos && inv.photos.length > 0) ? inv.photos[0] : (inv.image || null);

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
        title={inv.name}
        subtitle={inv.developer}
        extra={inv.district}
        onClick={onSelect}
        badges={
          <div className="usi-flex-row usi-gap-8">
            <SourceBadge source={inv.source} />
            {(inv.is_new || inv.reviewed === false) && <span className="usi-pill success usi-tiny">NOWE</span>}
          </div>
        }
        footerLeft={<CategoryStripe ratings={inv.ratings || {}} />}
        footerRight={CustomFooterRight || DefaultFooterRight}
      />
    );
  };

  const ListCard = React.memo(ListCardComponent, (prev, next) => {
    return prev.inv?.slug === next.inv?.slug && 
           prev.inv?.updated_at === next.inv?.updated_at &&
           prev.onSelect === next.onSelect;
  });

  usiRegister('ListCard', ListCard);
})();
