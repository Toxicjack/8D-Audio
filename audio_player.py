import argparse

from audio_processing import play_processed_audio, save_processed_audio
from versioning import VERSION, require_runtime_python

def main():
    require_runtime_python()
    parser = argparse.ArgumentParser(description="Play or save audio with 8D effects.")
    parser.add_argument('file', type=str, help="Path to the audio file to process.")
    parser.add_argument('--pan_speed', type=float, default=0.1, help="Panning speed for 8D effect.")
    parser.add_argument('--reverb_amount', type=float, default=0.3, help="Reverb amount for 8D effect.")
    parser.add_argument('--eq_gains', type=float, nargs='*', default=None, help="Equalizer gains for 10 frequency bands in dB.")
    parser.add_argument('--volume', type=float, default=1.0, help="Volume multiplier (1.0 is original volume).")
    parser.add_argument('--disable_surround', action='store_true', help="Disable the moving surround effect.")
    parser.add_argument('--output_device', type=int, help="Sounddevice output device index to use for playback.")
    parser.add_argument('--save', type=str, help="Path to save the processed audio file.")
    parser.add_argument('--version', action='version', version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    surround = not args.disable_surround
    eq_gains = args.eq_gains if args.eq_gains else None

    if args.save:
        print(f"Processing and saving {args.file} with 8D effects...")
        save_processed_audio(
            args.file,
            args.save,
            pan_speed=args.pan_speed,
            reverb_amount=args.reverb_amount,
            eq_gains=eq_gains,
            surround=surround,
            volume=args.volume,
        )
        print(f"Saved processed audio to {args.save}")
    else:
        print(f"Playing {args.file} with 8D effects...")
        play_processed_audio(
            args.file,
            pan_speed=args.pan_speed,
            reverb_amount=args.reverb_amount,
            eq_gains=eq_gains,
            surround=surround,
            volume=args.volume,
            device=args.output_device,
        )

if __name__ == "__main__":
    main()
