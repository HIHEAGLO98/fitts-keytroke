from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout,
    QHBoxLayout, QTextBrowser, QPushButton
)
from PySide6.QtCore import Qt

# Help content
_HELP_HTML = """
<h2>Qu'est-ce que la loi de Fitts ?</h2>
<p>
Cette application permet d'expérimenter la loi de Fitts. Basée sur une
équation mathématique, la loi de Fitts est utilisée afin de mettre en
évidence le temps nécessaire pour atteindre un objet cible. Quand on
se met dans le cadre de l'IHM, un objet cible est n'importe quel
élément interactif, comme un lien hypertexte, un bouton d'envoi ou
un champ de saisie dans un formulaire sur internet. Dans notre test,
les cibles seront des <span style="color:#e74c3c">ronds rouges</span>.
</p>

<h2>Formule de la loi de Fitts</h2>
<p style="font-size:20px; font-family: serif; margin: 12px 0;">
&nbsp;&nbsp;<i>T = a + b &middot; log<sub>2</sub>(1 + D / L)</i>
</p>
<p>
<b>T</b> représente le temps pour accomplir l'action, <b>a</b> et <b>b</b>
sont des constantes empiriques, <b>D</b> est la distance de l'objet cible
et <b>L</b> est la largeur de l'objet cible.
</p>

<h2>Déroulement du test</h2>
<p>
Une fois sur la page de test il vous faudra cliquer sur l'écran.
Le test se lance avec les paramètres saisis dans la page principale.
Des <span style="color:#e74c3c">cibles rouges</span>, sur lesquelles
il faut cliquer le plus rapidement, apparaîtront successivement.
</p>

<h2>Résultats du test</h2>
<p>
À la fin du test, deux graphiques seront affichés. Le premier affiche
le calcul de la loi de Fitts pour chaque cible du test et le second
le temps d'exécution en fonction de la distance relative.
</p>

<h2>Expériences Keystroke (GOMS)</h2>
<p>
Le modèle <b>GOMS/Keystroke</b> prédit le temps d'une commande
clavier/souris en combinant les opérateurs élémentaires :
</p>
<ul>
  <li><b>K</b> — frappe d'une touche (~200 ms)</li>
  <li><b>H</b> — transfert main clavier → souris (~400 ms)</li>
  <li><b>P</b> — déplacement de pointeur (~1100 ms)</li>
  <li><b>M</b> — préparation mentale (~1300 ms)</li>
</ul>
<p>
Les expériences K, H et C permettent de mesurer empiriquement ces
valeurs sur votre propre matériel et de les comparer aux valeurs
théoriques de référence.
</p>

<h2>Raccourcis clavier</h2>
<ul>
  <li><b>F1</b> — Ouvrir cette aide</li>
  <li><b>Ctrl+O</b> — Ouvrir un fichier (expérience C)</li>
</ul>
"""


class HelpDialog(QDialog):
    """
    Modal help dialog displaying application documentation.
    Plays a system beep when opened.
    """

    TITLE = "Aide - Loi de Fitts et Keystroke - HM40"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.TITLE)
        self.setMinimumSize(540, 620)
        self.resize(580, 680)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Scrollable HTML content
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(
            "QTextBrowser { border: none; padding: 24px; font-size: 14px; }"
        )
        self.browser.setHtml(_HELP_HTML)
        root.addWidget(self.browser, stretch=1)

        # OK button bar
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(16, 8, 16, 12)
        btn_bar.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(80)
        ok_btn.setStyleSheet(
            "QPushButton { background: #232a34; color: #f3f3f3; border: none; "
            "border-radius: 8px; padding: 8px 0; font-size: 14px; "
            "font-weight: 600; margin: 0; }"
            "QPushButton:hover { background: #2d3a4b; }"
        )
        ok_btn.clicked.connect(self.accept)
        btn_bar.addWidget(ok_btn)

        root.addLayout(btn_bar)

    def show_with_beep(self) -> None:
        """Play a beep then open the dialog modally."""
        QApplication.beep()
        self.exec()