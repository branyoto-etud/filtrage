# JPEG-2000 Compression

This is an implementation of the JPEG-2000 algorithm.
Source : http://d.xav.free.fr/ebcot/

This implementation uses only the base of the algorithm.

This is a proof-of-concept, and that's why the compressed file isn't writen
in a binary mode but in a human-readable mode.

The conversion between the two shouldn't be that hard:
 - replace file opening with binary mode
 - remove space and LF from buffer
 - replace contextes (ZCx, RL, MRx, SCx) by a binary number

And that's it I think.

The decompression isn't available atm, but will be soon or later.
As said, this is more of an exemple that the compression work than a real
program to compress images. If you want a real compression, internet
is plenty of online converter for images.
