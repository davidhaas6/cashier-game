from src.game_manager import GameManager

if __name__ == "__main__":
    gam = GameManager()
    try:
        gam.loop()
    except KeyboardInterrupt:
        print("Goodbye!")
