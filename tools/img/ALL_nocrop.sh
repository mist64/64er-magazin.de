#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <dir>"
  exit
else
  out=$1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

tmp1=$(mktemp).tiff
tmp2=$(mktemp).tiff
tmp_600=$(mktemp).tiff
tmp_150=$(mktemp).tiff

# A4 width and height at 150 DPI
a4_width=1240
a4_height=1754

out_600=${out}/600
out_150=${out}/150

mkdir -p ${out}
mkdir -p ${out_600}
mkdir -p ${out_150}

for in_filename in ???.png; do
	id="${in_filename%%.*}"

	out_filename_600="${out_600}/${id}_600.tiff"
	out_filename_150="${out_150}/${id}_150.tiff"
	if [ -e "$out_filename_600" ] && [ -e "$out_filename_150" ]; then
		echo "Skipping $in_filename"
		continue
	fi

	echo ${in_filename}

	echo "    * convert to CMYK"
	# convert to CMYK
	/usr/bin/python3 $SCRIPT_DIR/convert.py ${in_filename} ${tmp1}

	# increase channel contrast
	echo "    * increase contrast"
	magick ${tmp1} \
	-colorspace CMYK \
	-channel C -level 50%,90% \
	-channel M -level 30%,70% \
	-channel Y -level 30%,70% \
	-channel K -level 90%,95% \
	+channel -colorspace CMYK \
	-density 2400 -set units PixelsPerInch \
	"${tmp2}"

	rm "${tmp1}"

	echo "    * resize to 600 dpi"
	magick "${tmp2}" \
	-resize 25% \
	-profile $SCRIPT_DIR/USWebCoatedSWOP.icc \
	-profile $SCRIPT_DIR/AdobeRGB1998.icc \
	-density 600 -set units PixelsPerInch \
	"${tmp_600}"

	echo "    * resize to 150 dpi"
	magick "${tmp2}" \
	-resize 6.25% \
	-profile $SCRIPT_DIR/USWebCoatedSWOP.icc \
	-profile $SCRIPT_DIR/AdobeRGB1998.icc \
	-density 150 -set units PixelsPerInch \
	"${tmp_150}"

	rm "${tmp2}"

	# Crop to A4 width (always remove right border)
	a4_width_600=$((a4_width * 4))
	a4_height_600=$((a4_height * 4))

	crop_600="${a4_width_600}x${a4_height_600}+0+0"
	crop_150="${a4_width}x${a4_height}+0+0"

	echo "    * crop 600"
	magick "${tmp_600}" \
	-crop $crop_600 \
	-background white \
	-gravity west \
	-extent ${a4_width_600}x${a4_height_600} \
	"${out_filename_600}"

	echo "    * crop 150"
	magick "${tmp_150}" \
	-crop $crop_150 \
	-background white \
	-gravity west \
	-extent ${a4_width}x${a4_height} \
	"${out_filename_150}"

	rm "${tmp_600}"
	rm "${tmp_150}"

done
