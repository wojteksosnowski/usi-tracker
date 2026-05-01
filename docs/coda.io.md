
tabela: USImaster

nazwa przycisku: extraRP do DB
funkcja przycisku:

`ListCombine(
  thisRow.rpJSON.ParseJSON("$.main_image.m_img_1500").Trim(),
  PineMintRPUtils::FetchRawJsonFile(
    Concatenate(
      "https://rynekpierwotny.pl/api/v2/offers/offer/",
      thisRow.rpJSON.ParseJSON("$.id").Trim(),
      "/?s=offer-detail-gallery"
    )
  )
    .ParseJSON(
      "$.gallery.*.image.g_img_1500"
    )
)
  .Unique()
  .Filter(
    CurrentValue.IsNotBlank()
  )
  .ForEach(
    PineMintDropbox::DBFastSaveUrlToDropbox(
      [Wojtek Sosnowski],
      CurrentValue,
      Join(
        "/",
        "/Public/USI",
        thisRow.Deweloper.usiFolder,
        thisRow.USIfolder,
        RegexExtract(CurrentValue, "(?<=\/)[^\/]+\.(?:jpg|png)")
      )
        .Trim()
    )
  )`


nazwa przycisku: extraOTO do DB
funkcja przycisku:

`ListCombine(
  thisRow.otoJSON.ParseJSON("$.ad.images[*].large")
)
  .Unique()
  .ForEach(
    PineMintDropbox::DBFastSaveUrlToDropbox(
      [Wojtek Sosnowski],
      CurrentValue,
      Join(
        "/",
        "/Public/USI",
        thisRow.Deweloper.usiFolder,
        thisRow.USIfolder,
        Concatenate(
          RegexExtract(CurrentValue, "[^\/]+(?=\/im)"), ".webp"
        )
      )
    )
  )`

nazwa przycisku: rpProcesJSON
funkcja przycisku:

`ModifyRows(
  thisRow,
  thisRow.rpID,
  thisRow.rpJSON.ParseJSON("$.id").Trim(),
  thisRow.[Liczba Mieszkań],
  if(
    thisRow.[Liczba Mieszkań].IsBlank(),
    thisRow.rpJSON.ParseJSON("$.properties").Trim(),
    thisRow.[Liczba Mieszkań]
  ),
  thisRow.[Liczba Mieszkań],
  if(
    thisRow.[Liczba Mieszkań].IsBlank(),
    thisRow.rpJSON.ParseJSON("$.properties_for_sale_count")
      .Trim(),
    thisRow.[Liczba Mieszkań]
  ),
  thisRow.USIfolder,
  if(
    thisRow.USIfolder.IsBlank(),
    thisRow.rpJSON.ParseJSON("$.slug").Trim(),
    thisRow.USIfolder
  ),
  thisRow.strona_inwestycji,
  if(
    thisRow.strona_inwestycji.IsBlank() OR
      thisRow.strona_inwestycji = "/deweloperzy/",
    thisRow.rpJSON.ParseJSON("$.website").Trim(),
    thisRow.strona_inwestycji
  ),
  thisRow.Segment,
  If(
    thisRow.rpJSON.ParseJSON("$.type").Trim() = 2,
    [segmenty i domy],
    thisRow.Segment
  ),
  thisRow.[google-maps],
  Concatenate(
    "https://www.google.com/maps/@",
    thisRow.rpJSON.ParseJSON("$.$.geo_point.value.coordinates.value.[1]"),
    ",",
    thisRow.rpJSON.ParseJSON("$.$.geo_point.value.coordinates.value.[0]"),
    ",18z?hl=pl"
  )
)`


nazwa przycisku: OTOprocessJSON
funkcja przycisku: 

`ModifyRows(
  thisRow,
  thisRow.otoID,
  thisRow.otoJSON.ParseJSON("$.id").Trim(),
  thisRow.[Liczba Mieszkań],
  if(
    thisRow.[Liczba Mieszkań].IsBlank(),
    thisRow.otoJSON.ParseJSON("$.ad.characteristics[*]")
      .RegexExtract(
        '(?<=\"key\":\"number_of_properties\",\"value":\")(?:.*?)(?=\")'
      )
      .Trim(),
    thisRow.[Liczba Mieszkań]
  ),
  thisRow.USIfolder,
  if(
    thisRow.USIfolder.IsBlank(),
    thisRow.otoJSON.ParseJSON("$.ad.slug")
      .RegexExtract(
        "(?:.*)(?=-ID)"
      )
      .Trim(),
    thisRow.USIfolder
  ),
  thisRow.Termin,
  If(
    thisRow.Termin.IsBlank(),
    Concatenate(
      RoundDown(
        thisRow.otoJSON.ParseJSON("$.ad.characteristics[*]")
          .RegexExtract(
            '(?<=\"key\":\"finish_date\",\"value":\")(?:.*?)(?=\")'
          )
          .Trim()
          .ToDate()
          .Month() /
          4
      ) +
        1,
      " kw. ",
      thisRow.otoJSON.ParseJSON("$.ad.characteristics[*]")
        .RegexExtract(
          '(?<=\"key\":\"finish_date\",\"value":\")(?:.*?)(?=\")'
        )
        .Trim()
        .ToDate()
        .Year()
    ),
    thisRow.Termin
  )
)`

tabela relacyjna: USIOjciec
funkcja filtrująca tabelę: `USIlokalizacja = thisRow.USIlokalizacja AND CurrentValue!=thisRow`

nazwa zmiennej: USIlokalizacja
funkcja zmiennej: `Location(Ceiling(thisRow.Latitude, 0.01), Ceiling(thisRow.Longitude, 0.01))`

nazwa zmiennej: rpOpis
funkcja zmiennej: `Concatenate( thisRow.rpJSON.ParseJSON("$.description.root.children[*].children[*].text"))`

nazwa zmiennej: rpLokalizacja
funkcja zmiennej: `thisRow.rpJSON.ParseJSON("$.region.value.included_location.value.description")`

nazwa zmiennej: RPfacilities
funkcja zmiennej: 

`If(
  thisRow.rpJSON.ParseJSON("$.facilities.value").ListCombine()
    .IsBlank() OR thisRow.rpJSON.IsBlank(),
  "",
  [HasłaMarketingowe]
    .Filter(
      rpNo
        .Contains(
          thisRow.rpJSON.ParseJSON("$.facilities.value").ListCombine()
        )
    )
)`

nazwa zmiennej: OTOfeatures
funkcja zmiennej:

`[HasłaMarketingowe]
  .Filter(
    HMLabel
      .Contains(
        thisRow.otoJSON.ParseJSON("$.ad.features").ListCombine()
      )
  )`


nazwa zmiennej: Mapa
funkcja zmiennej:

`Concatenate(
  "https://image.maps.hereapi.com/mia/v3/base/mc/overlay:padding=64;zoom=16/1536x512/png?apiKey=BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c&overlay=point:",
  thisRow.POIx2,
  "|size=large;icon=bubble&style=explore.satellite.day&scaleBar=km&features=pois:disabled&lang=pl"
)`

---

przechwytywanie obrazów z różnych stron

nazwa zmiennej:
funkcja zmiennej: `ScraperAPI::ScrapeUrl(ScrapperAPIKey, pageToGrab)`


nazwa zmiennej: grabber-all
funkcja zmiennej:

`ForEach(
  GrabberSito,
  WithName(
    CurrentValue,
    Sito,
    [grabber-page]
      .RegexExtract(
        Sito.comp1, Sito.comp2
      )
      .ListCombine()
      .Unique()
      .FormulaMap(
        Concatenate(
          sito.comp3,
          PineMintStudiosUtils::MultiReplace(CurrentValue, "%3A", ":", "%2F", "/")
        )
      )
  )
)
  .Unique()
  .ListCombine()`


tablica: GrabberSito
## GrabberSito
|Name|comp1|comp2|comp3|Number|
|---|---|---|---|---|
|Atal|https:\/[^\"]*?(?:avif\|webp\|mp4\|jpg\|png\|jpeg)(?=\")|gms||0|
|SGI|(?<=\/_gatsby).*?(?:avif\|webp\|mp4\|jpg\|png\|jpeg)(?=\?)|gms|[https://www.sgi.pl/_gatsby](https://www.sgi.pl/_gatsby)|0|
|DomD|(?<=<a href="\/getmedia\/).*jpg(?=" class)|gm|[https://www.domd.pl/getmedia/](https://www.domd.pl/getmedia/)|0|
|Architektura i Biznez|https:\/\/cdn.a[^\"]+1920[^\"]+|gms||0|
|wordpress, Moderna|https:\/\/[^\"]*?(?:jpg\|webp\|avif\|mp4)(?=\")|gms||0|
|allcon|(?<=next\/image\?url\=)https.*?(?:avif\|webp\|mp4\|jpg\|png\|jpeg\|JPG).*?(?=&)|gms||0|
|robyg gdańsk|(?<=next\/image\?url\=)%.*?(?:avif\|webp\|mp4\|jpg\|png\|jpeg\|JPG\|svg).*?(?=&)|gms|[https://gdansk.robyg.pl](https://gdansk.robyg.pl)|0|
|Domesta|(?<=url\()\/mm.*?(?:avif\|webp\|mp4\|jpg\|png\|jpeg\|JPG).*?(?=\))|gms|[https://www.domesta.com.pl](https://www.domesta.com.pl)|0|
|Sztuka architektury|\/assets[^\"]*?(?:avif\|webp\|mp4\|jpg\|png\|jpeg)(?=\")|gms|[https://sztuka-architektury.pl](https://sztuka-architektury.pl)|0|
|Gutenberga|\/static[^\"]*?(?:webp)(?=\")|gms|[https://apartamentygutenberga.pl](https://apartamentygutenberga.pl)|0|


---

