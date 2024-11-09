rm -rf new
mkdir new

mkdir new/k
(cd img/k; for i in *; do echo $i; magick $i -colorspace CMYK -channel K -separate +channel -threshold 50% -negate ../../new/k/$i; done)

# K channel -> 150 dpi gray
mkdir new/gray
(cd img/gray; for i in *; do echo $i; magick $i -colorspace CMYK -channel K -separate +channel -negate -resize 25% ../../new/gray/$i; done)

# CMYK -> 150 dpi color
mkdir new/col
(cd img/col; for i in *; do echo $i; magick $i -resize 25% ../../new/col/$i; done)

# K channel with K-pattern -> 600 dpi bilevel
mkdir new/kdot
(cd img/kdot; for s in `seq 20 40`; do for i in *; do echo $i; magick $i -colorspace CMYK -channel K -separate +channel -negate -threshold $s% ../../new/kdot/$i-$s.png; done; done)
