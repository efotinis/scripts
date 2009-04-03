function BinarySearchResult(found, pos) {
  this.found = found;
  this.pos = pos;
}
function binarySearch(a, x) {
  var i = 0;
  var j = a.length;
  while (i < j) {
    var k = Math.floor((i + j) / 2);
    if (x == a[k])
      return new BinarySearchResult(true, k);
    if (x < a[k])
      j = k;
    else
      i = k + 1;
  }
  return new BinarySearchResult(false, i);
}


