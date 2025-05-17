#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <dir>"
  exit
else
  out=$1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# A4 width and height at 150 DPI
a4_width=1240
a4_height=1754

out_600=${out}/600
out_150=${out}/150
out_cropped=${out}/cropped
out_600_cropped=${out}/600_cropped

mkdir -p ${out}
mkdir -p ${out_600}
mkdir -p ${out_150}
mkdir -p ${out_cropped}
mkdir -p ${out_600_cropped}

for in_filename in ???.png; do
	id="${in_filename%%.*}"
	
	out_filename_600="${out_600}/${id}_600.tiff"
	out_filename_150="${out_150}/${id}_150.tiff"
	out_filename_150_cropped="${out_cropped}/${id}_150_cropped.tiff"
	out_filename_600_cropped="${out_600_cropped}/${id}_600_cropped.png"
	if [ -e "$out_filename_600" ] && [ -e "$out_filename_150" ] && [ -e "$out_filename_150_cropped" ] && [ -e "$out_filename_600_cropped" ]; then
		echo "Skipping $in_filename"
		continue
	fi

	echo ${in_filename}

	echo "    * convert to b/w"
	magick ${in_filename} \
	-colorspace CMYK \
	-channel K \
	-separate \
	+channel \
	-threshold 65% \
	-negate \
	-density 600 -set units PixelsPerInch \
	"${out_filename_600}"
	
	echo "    * resize to 150 dpi"
	magick "${out_filename_600}" \
	-resize 25% \
	-density 150 -set units PixelsPerInch \
	"${out_filename_150}"

	echo "    * get width"
	# get crop info from widths file
	crop_width=$(grep "^${id}:" widths.txt | cut -d ':' -f 2 | tr -d ' ')

	# get current width, so we can crop on the left
	width=$(magick identify -format "%w" "${out_filename_150}") 

	if [ $((10#$id % 2)) -eq 0 ]; then
		# Even page: crop starting from the calculated offset (right side), extend on the left
		crop="${crop_width}x${a4_height}+0+0"
		gravity="east"
	else
		# Odd page: crop starting from 0 (left side), extend on the right
		offset=$(($width - $crop_width))
		crop="${crop_width}x${a4_height}+${offset}+0"
		gravity="west"
	fi
	
	echo ${in_filename} ${crop_width} ${crop} ${gravity}
	
	echo "    * crop 150"
	magick "${out_filename_150}" \
	+repage \
	-crop $crop \
	-background white \
	-gravity $gravity \
	-extent ${a4_width}x${a4_height} \
	"${out_filename_150_cropped}"

	a4_width_600=$((a4_width * 4))
	a4_height_600=$((a4_height * 4))
	crop_width_600=$((crop_width * 4))
	width_600=$(magick identify -format "%w" "${out_filename_600}") 
	
	#echo $width_600 $crop_width $crop_width_600
	
	if [ $((10#$id % 2)) -eq 0 ]; then
		# Even page: crop starting from the calculated offset (right side), extend on the left
		crop_600="${crop_width_600}x${a4_height_600}+0+0"
		gravity="east"
	else
		# Odd page: crop starting from 0 (left side), extend on the right
		offset_600=$(($width_600 - $crop_width_600))
		crop_600="${crop_width_600}x${a4_height_600}+${offset_600}+0"
		gravity="west"
	fi

	echo "    * crop 600"
	magick "${out_filename_600}" \
	+repage \
	-crop $crop_600 \
	-background white \
	-gravity $gravity \
	-extent ${a4_width_600}x${a4_height_600} \
	"${out_filename_600_cropped}"

done < widths.txt
