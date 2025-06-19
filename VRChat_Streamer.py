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
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        print(f"Error: Could not access webcam {selected_camera}.")
        return

    # === Constants ===
    WIDTH, HEIGHT = 16, 14
    PIXELS_PER_BYTE = 4
    BITS_PER_PIXEL = 2
    channel_map = [2, 1, 0]  # OpenCV BGR to RGB

    # === Pixel Buffers ===
    channel_buffers = {
        0: np.zeros((HEIGHT, WIDTH), dtype=np.uint8),  # R
        1: np.zeros((HEIGHT, WIDTH), dtype=np.uint8),  # G
        2: np.zeros((HEIGHT, WIDTH), dtype=np.uint8),  # B
    }

    def interlace(image, even_rows=True):
        """Extract only even or odd rows from the image."""
        interlaced = np.zeros_like(image)
        if even_rows:
            interlaced[::2] = image[::2]
        else:
            interlaced[1::2] = image[1::2]
        return interlaced

    def send_osc_param(name, value):
        msg = osc_message_builder.OscMessageBuilder(address=name)
        if isinstance(value, (np.integer, np.uint8)):
            msg.add_arg(int(value))
        elif isinstance(value, (np.floating, np.float32)):
            msg.add_arg(float(value))
        else:
            msg.add_arg(value)
        client.send(msg.build())

    def pack_2bit_row(row):
        """Pack 4 2-bit pixels into one byte."""
        packed = []
        for j in range(0, WIDTH, PIXELS_PER_BYTE):
            byte = 0
            for k in range(PIXELS_PER_BYTE):
                if j + k < WIDTH:
                    byte |= (row[j + k] & 0x03) << (2 * k)
            packed.append(byte)
        return packed

    even_rows = True
    color_channel = 0  # 0=R, 1=G, 2=B

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image.")
                break

            # === Aspect Ratio ===
            h, w = height, width
            send_osc_param("/avatar/parameters/Ratio", (w / h) - 1)

            # === Resize to 16x14 ===
            small_image = cv2.resize(frame, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)

            for i in range(6):
                # === Set color channel ===
                raw_channel = small_image[:, :, channel_map[color_channel]]
                quantized = np.clip(raw_channel // 64, 0, 3).astype(np.uint8)
                # === Update Buffer & Interlace ===
                channel_buffers[color_channel] = quantized
                interlaced = interlace(quantized, even_rows)

                # === Preview ===
                b = (channel_buffers[0] * 85).astype(np.uint8)
                g = (channel_buffers[1] * 85).astype(np.uint8)
                r = (channel_buffers[2] * 85).astype(np.uint8)
                preview = cv2.resize(
                    np.stack([r, g, b], axis=-1),
                    (int(150 * (w / h)), 150),
                    interpolation=cv2.INTER_AREA,
                )
                cv2.imshow("Color Preview", preview)

                # === Send Control Flags ===
                send_osc_param("/avatar/parameters/RG", 1 if color_channel == 1 else 0)
                send_osc_param("/avatar/parameters/B", 1 if color_channel == 2 else 0)
                send_osc_param("/avatar/parameters/interlacing_flag", even_rows)

                # === Send Image Data ===
                for i in range(HEIGHT):
                    if (i % 2 == 0) == even_rows:
                        packed = pack_2bit_row(interlaced[i])
                        row_index = i // 2
                        for j, byte in enumerate(packed):
                            send_osc_param(f"/avatar/parameters/webcam_pixel/{row_index}_{j}", byte)

                # === Cycle State ===
                color_channel = (color_channel + 1) % 3
                even_rows = not even_rows
                time.sleep(0.11)

            # === Quit Key ===
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Stream interrupted by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", type=int, required=True)
    parser.add_argument("--resolution", type=str, required=True)
    args = parser.parse_args()
    main(args.camera, args.resolution)
