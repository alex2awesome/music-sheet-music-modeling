
from MusicSynthGen import VerovioGenerator

def main(gt_samples_path):
    gen = VerovioGenerator(gt_samples_path)
    print("VerovioGenerator initialized.")
    try:
        score, tokens = verovio_gen.generate_score(num_sys_gen=1)
        print("Score and tokens generated.")
        cv2.imwrite("generated_score.png", score)
        print("Generated score saved as 'generated_score.png'.")
        print("Generated Score Tokens:", tokens)
    except Exception as e:
        print(f"Error during score generation: {e}")