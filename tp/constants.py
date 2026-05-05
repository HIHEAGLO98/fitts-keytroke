import math

# Experiment Settings
NUM_TARGETS: int = 5
TARGET_MIN_SIZE: int = 30
TARGET_MAX_SIZE: int = 70

# Default regression coefficients for Fitts' law: T = a + b * log2(D/W + 1)
DEFAULT_A: float = 0.1
DEFAULT_B: float = 0.1


def calculate_expected_time(d: float, w: float) -> float:
    """
    Calculate expected time using Fitts' Law: T = a + b * log2(D/W + 1).

    Args:
        d (float): Distance from the previous target's center.
        w (float): Width of the current target.

    Returns:
        float: Expected time to acquire the target.
    """
    return DEFAULT_A + DEFAULT_B * math.log2(d / w + 1) if w > 0 else 0.0


# Application settings (can be modified in settings screen)
class Settings:
    """
    Class to store application settings.
    """
    num_targets: int = NUM_TARGETS
    target_min_size: int = TARGET_MIN_SIZE
    target_max_size: int = TARGET_MAX_SIZE
    a_coefficient: float = DEFAULT_A
    b_coefficient: float = DEFAULT_B
    theme: str = "dark"
    language: str = "fr"

    @classmethod
    def reset_to_defaults(cls) -> None:
        cls.num_targets = NUM_TARGETS
        cls.target_min_size = TARGET_MIN_SIZE
        cls.target_max_size = TARGET_MAX_SIZE
        cls.a_coefficient = DEFAULT_A
        cls.b_coefficient = DEFAULT_B
        cls.theme = "dark"
        cls.language = "fr"


TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "app_title": "Experiences Fitts & Keystroke",
        "choose_experiment": "Choisissez une experience",
        "fitts_experiment": "Experience de Fitts",
        "keystroke_experiment": "Experience Keystroke",
        "hover_fitts_desc": "Pointez et cliquez des cibles pour visualiser la loi de Fitts.",
        "hover_keys_desc": "Mesurez les performances de saisie clavier selon les conditions.",
        "default_menu_help": "Survolez une carte pour afficher une mini explication.",
        "fitts_intro": "Cliquez sur Demarrer pour lancer le test de Fitts",
        "fitts_law_title": "Loi de Fitts",
        "fitts_law_short": "Le temps de mouvement depend de la distance D et de la taille W de la cible.",
        "show_fitts_law": "Afficher explication",
        "start": "Demarrer",
        "countdown_label": "Debut dans {seconds}...",
        "running_label": "Test en cours...",
        "target_hint": "Cliquez la cible rouge pour continuer.",
        "x_axis": "Axe X :",
        "target_number": "Numero de cible",
        "time": "Temps",
        "difficulty_index": "Indice de difficulte",
        "coef_a": "Coefficient a :",
        "coef_b": "Coefficient b :",
        "back_menu": "Menu",
        "restart": "Recommencer",
        "zoom_reset": "Zoom",
        "actual_time": "Temps réel",
        "expected_time": "Temps attendu",
        "fitts_law": "Loi de Fitts",
        "final_results": "Resultats finaux",
        "live_results": "Resultats en direct",
        "theme": "Theme",
        "language": "Langue",
        "dark": "Noir",
        "light": "Blanc",
        "file_menu": "Fichier",
        "navigation_menu": "Navigation",
        "exit": "Quitter",
        "main_menu": "Menu principal",
        "keystroke_experiments": "Experiences Keystroke",
        "settings": "Parametres",
        "settings_title": "Parametres de l'experience",
        "target_count": "Nombre de cibles",
        "number_of_targets": "Nombre de cibles :",
        "target_size_range": "Taille des cibles",
        "min": "Min :",
        "max": "Max :",
        "fitts_coefficients": "Coefficients de la loi de Fitts",
        "appearance": "Apparence",
        "apply_coefficients": "Appliquer les coefficients",
        "save_all_settings": "Enregistrer",
        "reset_defaults": "Valeurs par defaut",
        "keystroke_menu_title": "Choisissez une experience Keystroke",
        "cognitive_load_btn": "Impact de la charge cognitive sur la frappe",
        "navigation_btn": "Efficacite navigation clavier vs souris",
        "back_keystroke_menu": "Menu Keystroke",
    },
    "en": {
        "app_title": "Fitts & Keystroke Experiments",
        "choose_experiment": "Choose an Experiment",
        "fitts_experiment": "Fitts Experiment",
        "keystroke_experiment": "Keystroke Experiment",
        "hover_fitts_desc": "Point and click targets to visualize Fitts' law behavior.",
        "hover_keys_desc": "Measure keyboard performance under different constraints.",
        "default_menu_help": "Hover a card to read a short explanation.",
        "fitts_intro": "Click Start to begin the Fitts experiment",
        "fitts_law_title": "Fitts' Law",
        "fitts_law_short": "Movement time depends on distance D and target width W.",
        "show_fitts_law": "Show explanation",
        "start": "Start",
        "countdown_label": "Starting in {seconds}...",
        "running_label": "Experiment running...",
        "target_hint": "Click the red target to continue.",
        "x_axis": "X-Axis:",
        "target_number": "Target Number",
        "time": "Time",
        "difficulty_index": "Index of Difficulty",
        "coef_a": "Coefficient a:",
        "coef_b": "Coefficient b:",
        "back_menu": "Menu",
        "restart": "Restart",
        "zoom_reset": "Zoom",
        "actual_time": "Actual Times",
        "expected_time": "Expected Times",
        "fitts_law": "Fitts' Law",
        "final_results": "Final results",
        "live_results": "Live results",
        "theme": "Theme",
        "language": "Language",
        "dark": "Dark",
        "light": "Light",
        "file_menu": "File",
        "navigation_menu": "Navigation",
        "exit": "Exit",
        "main_menu": "Main Menu",
        "keystroke_experiments": "Keystroke Experiments",
        "settings": "Settings",
        "settings_title": "Experiment Settings",
        "target_count": "Target Count",
        "number_of_targets": "Number of Targets:",
        "target_size_range": "Target Size Range",
        "min": "Min:",
        "max": "Max:",
        "fitts_coefficients": "Fitts' Law Coefficients",
        "appearance": "Appearance",
        "apply_coefficients": "Apply Coefficients",
        "save_all_settings": "Save All Settings",
        "reset_defaults": "Reset to Defaults",
        "keystroke_menu_title": "Choose a Keystroke Experiment",
        "cognitive_load_btn": "Cognitive Load Impact on Typing Performance",
        "navigation_btn": "Keyboard vs. Mouse Text Navigation Efficiency",
        "back_keystroke_menu": "Keystroke Menu",
    },
}


def t(key: str) -> str:
    language = Settings.language if Settings.language in TRANSLATIONS else "en"
    return TRANSLATIONS[language].get(key, key)