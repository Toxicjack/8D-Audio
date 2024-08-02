import argparse
from audio_processing import play_processed_audio, save_processed_audio

def main():
    parser = argparse.ArgumentParser(description="Play or save audio with 8D effects.")
    parser.add_argument('file', type=str, help="Path to the audio file to process.")
    parser.add_argument('--pan_speed', type=float, default=0.1, help="Panning speed for 8D effect.")
    parser.add_argument('--reverb_amount', type=float, default=0.3, help="Reverb amount for 8D effect.")
    parser.add_argument('--eq_gains', type=float, nargs='*', default=None, help="Equalizer gains for different frequency bands.")
    parser.add_argument('--save', type=str, help="Path to save the processed audio file.")

    args = parser.parse_args()

    if args.save:
        print(f"Processing and saving {args.file} with 8D effects...")
        save_processed_audio(args.file, args.save, pan_speed=args.pan_speed, reverb_amount=args.reverb_amount, eq_gains=args.eq_gains)
        print(f"Saved processed audio to {args.save}")
    else:
        print(f"Playing {args.file} with 8D effects...")
        play_processed_audio(args.file, pan_speed=args.pan_speed, reverb_amount=args.reverb_amount, eq_gains=args.eq_gains)

if __name__ == "__main__":
    main()
