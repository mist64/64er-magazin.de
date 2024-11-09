import os
import sys

count = len(sys.argv[1:])

if count == 0:
	print(f"Usage: {sys.argv[0]} *.png");
	exit(1)

if count % 4:
	print(f"Error: file count not divisible by 4!");
	exit(1)


src = 0
a = count
b = 1
mid = a / 2
which = 0

while True:
	if src == 0:
		src_fn = f"\"Scan.png\""
	else:
		src_fn = f"\"Scan {src}.png\""	

	if which == 0:
		os.system(f"mv {src_fn} {a:03d}.png")
		if a % 2 == 0:
			which = 1
		a -= 1
	else:
		os.system(f"mv {src_fn} {b:03d}.png")
		if b % 2 == 0:
			which = 0
		b += 1

	if a < mid + 1 or b > mid + 1:
		break

	src += 1
