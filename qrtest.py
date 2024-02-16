import segno

# Path to your local PNG file
local_file_path = './static/flatlinelogo.png'

# v5 with h can contain 44 characters.
# Versions are from v1 to v40, the bigger the version the more data stored.
qrcode = segno.make('MATRIX-A9-Black Dragons-267F-13', error='h', version=5)

# Open the local PNG file
bg_file = open(local_file_path, 'rb')

# Generate the artistic QR code
qrcode.to_artistic(background=bg_file, target='MATRIX-A9-Black Dragons-267F-13.png', scale=9)

# Close the file
bg_file.close()
