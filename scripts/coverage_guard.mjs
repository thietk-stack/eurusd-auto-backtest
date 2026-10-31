// Coverage audit for source-verified monthly FX H1 CSV caches.
// A correct SHA proves file integrity, NOT that it covers the requested interval.
// Date endpoints are UTC and exclusive. Missing/invalid coverage fails closed.
export function coversRequestedInterval(metadata, requestedFrom, requestedTo) {
  const rawEnd=metadata.to_exclusive ?? metadata.to;
  const oldFrom=Date.parse(metadata.from);
  const oldTo=Date.parse(rawEnd);
  const needFrom=+requestedFrom;
  const needTo=+requestedTo;
  if (![oldFrom,oldTo,needFrom,needTo].every(Number.isFinite) ||
      oldTo<=oldFrom || needTo<=needFrom)
    throw Error('Invalid cached or requested historical quote interval');
  return oldFrom<=needFrom && oldTo>=needTo;
}
