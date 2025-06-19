import time
import cv2
import numpy as np
from pythonosc import udp_client
from pythonosc import osc_message_builder

def main(selected_camera, resolution):
    width, height = map(int, resolution.split("x"))

    # === OSC Setup ===
    osc_address = "127.0.0.1"
    osc_port = 9000
    client = udp_client.SimpleUDPClient(osc_address, osc_port)

    # === Webcam Setup ===
    cap = cv2.VideoCapture(selected_camera)
    if not cap.isOpened():
        print(f"Error: Could not access webcam {selected_camera}.")
        return

    # === Constants ===
    WIDTH, HEIGHT = 16, 14
    PIXELS_PER_BYTE = 4
    BITS_PER_PIXEL = 2

    def interlace(image, even_rows=True):
        interlaced = np.zeros_like(image)
        if even_rows:
            interlaced[::2] = image[::2]
        else:
            interlaced[1::2] = image[1::2]
        return interlaced

    def send_osc_param(name, value):
        msg = osc_message_builder.OscMessageBuilder(address=name)
        msg.add_arg(int(value) if isinstance(value, (np.integer, np.uint8)) else value)
        client.send(msg.build())

    def pack_2bit_row(row):
        packed = []
        for j in range(0, WIDTH, PIXELS_PER_BYTE):
            byte = 0
            for k in range(PIXELS_PER_BYTE):
                if j + k < WIDTH:
                    byte |= (row[j + k] & 0x03) << (2 * k)
            packed.append(byte)
        return packed

    buffer = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    even_rows = True

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image.")
                break

            send_osc_param("/avatar/parameters/Ratio", (width / height) - 1)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
            quantized = np.clip(resized // 64, 0, 3).astype(np.uint8)
            buffer[:, :] = quantized

            interlaced = interlace(buffer, even_rows)

            # Show grayscale preview (no interlacing lines)
            gray_preview = (quantized * 85).astype(np.uint8)
            gray_preview = cv2.resize(gray_preview, (int(150 * (width / height)), 150), interpolation=cv2.INTER_AREA)
            cv2.imshow("Grayscale Preview", gray_preview)

            send_osc_param("/avatar/parameters/RG", 1)
            send_osc_param("/avatar/parameters/B", 1)

            send_osc_param("/avatar/parameters/interlacing_flag", even_rows)

            for i in range(HEIGHT):
                if (i % 2 == 0) == even_rows:
                    packed = pack_2bit_row(interlaced[i])
                    row_index = i // 2
                    for j, byte in enumerate(packed):
                        send_osc_param(f"/avatar/parameters/webcam_pixel/{row_index}_{j}", byte)

            even_rows = not even_rows
            time.sleep(0.11)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Stream interrupted.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
