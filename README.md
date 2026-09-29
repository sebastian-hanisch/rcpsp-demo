# RCPSP – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-rcpsp-demo.streamlit.app/)**

Elftes und **letztes** Stück der **Klassische-Scheduling-Theorie-Linie** der "Konzepte"-Reihe für die Website
"Sebastian Hanisch – Operations Research und Machine Learning", der **wachsende Endpunkt**: statt einer neuen
Regel oder eines neuen Verfahrens wird hier das GESAMTE Job-Shop-Modell (Stück 8-10) selbst verallgemeinert -
**Ressourcen** statt nur Maschinen (Kapazität ≥ 1 statt nur 1, mehrere Aktivitäten können eine Ressource
gleichzeitig belegen) und ein **allgemeiner Vorranggraph** statt nur einer festen Kette pro Auftrag.

**Einordnung in die Linie:**
```
SPT (Wurzel) → EDD → Moore-Hodgson → WSPT → ATC → Johnson → LPT → Job Shop (Konvergenzpunkt, Stück 8)
                                                                       ├─ Shifting Bottleneck (Stück 9)
                                                                       ├─ Job-Shop-Tabu-Search (Stück 10)
                                                                       └─ RCPSP (dieses Stück - wachsender Endpunkt)
```
**Job Shop ist der Spezialfall Kapazität=1 überall + reine Kette** - strukturell IDENTISCH, nicht nur ähnlich:
per zwei unabhängigen CP-SAT-Modellen bestätigt (`AddCumulative` gegen `AddCircuit`, siehe Verifikation).
**LFT** (Latest Finish Time, Kolisch 1995, WebSearch-verifiziert als eine der besten klassischen
RCPSP-Prioritätsregeln) ist die RCPSP-Verallgemeinerung von Giffler-Thompson/MWKR (Stück 8) - eine serielle
Konstruktion, die bei jedem Schritt die dringendste zulässige Aktivität wählt. **CP-SAT über `AddCumulative`**
ist technisch NEU für diese Linie (Stück 6-10 nutzten `AddCircuit` für Maschinenreihenfolgen).

Ergebnis in Kürze: bei 5 Ketten über 4 Ressourcen (Standard-Seed, Job-Shop-Äquivalent) liegt **LFT** **49,3 %**
unter SPT, **17,3 %** unter FIFO, **23,9 %** unter einer zufälligen Priorität - und nur **4,2 %** über dem
bewiesenen CP-SAT-Optimum. **Der zentrale Beweis-Check dieses Stücks**: Kapazität=1 + reine Kette trifft EXAKT
das Job-Shop-Optimum (100 % über mehrere Instanzen, zwei strukturell unabhängige CP-SAT-Modelle). **Die zwei
Experimente, die das wachsende Beispiel ausmachen**: mehr Ressourcenkapazität senkt Cmax (86 → 57 bei
Kapazität 1 → 3, dann Konvergenz - mehr Kapazität hilft nichts mehr, sobald die Vorrang-Schranke selbst
bindet), mehr Vorrangdichte erhöht Cmax (86 → 190 bei Dichte 0 → 0,6, sauber monoton). **Überraschend schnell**:
CP-SAT über `AddCumulative` bleibt selbst bei 40 Aktivitäten unter 25 ms - deutlich schneller als das
Kreis-Modell (`AddCircuit`) aus Stück 6-10 bei vergleichbarer Größe.

| Frage | Ergebnis (Standardfall bzw. Mittel über 5 feste Instanzen) |
|---|---|
| Standardfall (5 Ketten, 4 Ressourcen, Kapazität 1) | ✅ LFT **49,3 %** unter SPT, nur **4,2 %** über dem CP-SAT-Optimum |
| **Kollaps-Test: Kapazität=1 + reine Kette == Job Shop** | ✅ **100 %** exaktes Optimum-Match (zwei unabhängige CP-SAT-Modelle) |
| **Mehr Ressourcenkapazität** | ✅ Cmax fällt (86→57), konvergiert gegen die reine Vorrang-Schranke |
| **Mehr Vorrangdichte** | ❌ Cmax wächst sauber monoton (86→190 bei Dichte 0→0,6) |
| **LFT auf JEDER Instanz mindestens so gut wie SPT?** | ❌ Nein - n_jobs=3, m=5, Seed 15: SPT klar vorn |

## Was die Demo zeigt

1. **RCPSP in Aktion** (Schritt-Slider): **Aktivitäten** (gestapelter Balken je Kette in Kettenposition, Farbe
   nach primärer Ressource) → **Einplanen** (Regler "eingeplante Aktivitäten", Gantt mit EINER ZEILE JE
   RESSOURCEN-SLOT - neu für diese Linie: bei Kapazität >1 bekommt eine Ressource mehrere Zeilen für parallele
   Belegungen, per gieriger Intervallfärbung zugewiesen) → **Ergebnis** (Fertigstellung je Ressource, LFT gegen
   SPT).
2. **Was die Prioritätsregel bringt:** LFT, SPT (die Wurzel dieser Linie - hier oft die falsche Regel), FIFO,
   Zufall, CP-SAT-Gegenprobe (n ≤ 20, mit Beweis-Status).
3. **📐 Sweep** über die Anzahl der Ketten ODER Ressourcen.
4. **🔬 Experimente auf Abruf:** wie stark hilft mehr Ressourcenkapazität; wie teuer ist zusätzlicher Vorrang -
   die zwei Experimente, die das wachsende Beispiel dieses Stücks ausmachen; Rechenzeit CP-SAT gegen die
   serielle Konstruktion.
5. **🚧 Grenzen:** Tabelle mit den echten Einschränkungen des Modells (nur eine Ressource je Aktivität, nur
   erneuerbare Ressourcen, keine Multi-Mode-Wahl).

Regler: Ketten (2–10), **Ressourcen** (2–6), **Kapazität je Ressource** (1–4), **zusätzliche Vorrangdichte**
(0–0,6), Seed der Instanz (+ 🎲). **Kein Vehikel-Umschalter** - bewusste Abweichung vom Linien-Muster, siehe
unten.

## Bewusste Abweichung vom Zwei-Vehikel-Muster dieser Linie

Jedes Stück 1-10 dieser Linie hat einen Vehikel-Umschalter (Neutral/Werkstatt-Logistik mit Rüstzeiten). Für
RCPSP lässt sich ein sauberes "Vehikel B = Rüstzeit" nicht mehr sinnvoll definieren: bei Kapazität >1 nutzen
MEHRERE Aktivitäten eine Ressource GLEICHZEITIG, es gibt keinen eindeutigen "Wechsel" mehr, an dem eine Rüstzeit
anfallen könnte. Statt eine künstliche Variante zu erzwingen: **EIN Modell, EIN wachsendes Beispiel** - die
Regler "Ressourcenkapazität" und "Vorrangdichte" SIND das wachsende Beispiel dieses Stücks (bei Kapazität=1 und
Dichte=0 exakt Job Shop, siehe Kollaps-Test). Mit dem Nutzer vorab abgestimmt und bewusst so freigegeben.

## Modell und Verfahren

- **Instanz** (`rcpsp_scenario.py`): `n_jobs` Ketten über `m_resources` Ressourcen (wie Job-Shop-Routing) plus
  zwei Regler, die das Modell verallgemeinern: `capacity` (Kapazität jeder Ressource) und `density`
  (zusätzliche Vorrangkanten zwischen VERSCHIEDENEN Ketten, nur in aufsteigender Aktivitäts-ID - garantiert
  azyklisch).
- **CPM-Schranken** (`rcpsp_algorithm.cpm_bounds`): klassische Netzplantechnik OHNE Ressourcen - früheste/
  späteste Start-/Endzeit je Aktivität per Vorwärts-/Rückwärtslauf über den Vorranggraphen.
- **Serielle Konstruktion** (`rcpsp_algorithm.serial_sgs`): baut EINEN zulässigen Zeitplan per Prioritätsregel
  (LFT, SPT, FIFO, Zufall) - bei jedem Schritt die zulässige Aktivität mit der höchsten Priorität zum
  frühesten ressourcenzulässigen Zeitpunkt einplanen.
- **CP-SAT** (`rcpsp_algorithm.solve_exact`): ein `NewIntervalVar` je Aktivität, `AddCumulative` je Ressource -
  anders als das Kreis-Modell (Stück 6-10) keine explizite Reihenfolge-Entscheidung nötig.
- **Auswertung** (`rcpsp_evaluation.py`): Kennzahlen, Sweep, Kapazitäts-/Vorrang-Experimente, Timing-Messreihe.

## Was nicht funktioniert hat / Grenzen

- **Ein echter Bug im Instanz-Generator gefunden und behoben:** die erste Fassung zog Ressourcenbedarf und
  Kapazität unabhängig voneinander - konnte eine Aktivität erzeugen, die MEHR von einer Ressource braucht, als
  diese überhaupt hat (z. B. Kapazität 1, Bedarf 2), eine von vornherein UNLÖSBARE Instanz. Gefunden beim ersten
  Testlauf der seriellen Konstruktion (`RuntimeError: Horizont zu klein` - die Suche nach einem zulässigen
  Startzeitpunkt lief bis zum Ende des Horizonts, ohne je ein passendes Fenster zu finden). Fix: Bedarf wird
  beim Erzeugen auf die Kapazität der jeweiligen Ressource gedeckelt (`np.minimum(demand, capacity)`).
- **Vorab-Annahme: "LFT ist auf dem Standard-Fall immer klar besser"** - **mit Einschränkung bestätigt**: im
  Mittel über die Sweep-Instanzen ja (12,4 % über SPT), aber NICHT auf jeder einzelnen Instanz (n_jobs=3, m=5,
  Kapazität 1, Seed 15: SPT schlägt LFT). Dieselbe ehrliche Lehre wie in Stück 7-10 dieser Linie - eine sehr
  gute Regel ist keine bewiesen optimale.
- **Nur eine Ressource je Aktivität, Bedarf immer 1**: eine bewusste Vereinfachung für Erklärbarkeit und eine
  saubere Gantt-Visualisierung (Slot-Zuweisung per Intervallfärbung setzt Bedarf 1 voraus). Echtes RCPSP erlaubt
  beliebigen Bedarf über mehrere Ressourcen gleichzeitig.
- **Nur erneuerbare Ressourcen, keine Multi-Mode-Wahl**: siehe 🚧-Tabelle in der App.

## Verifikation

- **Kollaps-Test (der zentrale Beweis-Check dieses Stücks)**: für n_jobs/m = (2,2), (3,2), (3,3), (4,3), mehrere
  Seeds - RCPSP mit Kapazität=1 + reiner Kette trifft EXAKT das Optimum eines UNABHÄNGIGEN Job-Shop-Kreis-
  Modells (`AddCircuit`, wie in `job-shop-demo`/`shifting-bottleneck-demo`/`job-shop-tabu-demo`) - zwei
  strukturell verschiedene CP-SAT-Formulierungen, dasselbe Ergebnis.
- **CPM-Schranken per Handrechnung**: eine 3-Aktivitäten-Kette und ein Parallelzweig mit bekanntem Puffer
  bestätigen ES/EF/LS/LF.
- **Zulässigkeits-Zertifikat**: die serielle Konstruktion respektiert Vorrang UND zu JEDEM Zeitpunkt die
  Kapazität jeder Ressource (direkt nachgerechnet, nicht nur angenommen).
- **Serielle Konstruktion nie unter dem CP-SAT-Optimum.**
- **Monotonie-Eigenschaften direkt geprüft**: mehr Kapazität kann Cmax nur senken oder gleich lassen, nie
  erhöhen; mehr Vorrangdichte kann Cmax nur erhöhen oder gleich lassen, nie senken.
- **Alle Zahlen der App-Texte sind als Tests hinterlegt** (Standardfall, Kapazitäts-/Vorrang-Experimente,
  Timing); alle 5 Presets geprüft; AppTest-Rauchtests (Voreinstellung, jedes Preset, jeder Schritt, Würfel-
  Knopf, Permalink-Grenzen, Extremwerte, Experimente auf Abruf, Footer, korrekt formatierte negative
  Prozent-Abstände).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: Schritte, Ergebnis, 📐 Sweep, 🔬 Experimente, 🚧 Grenzen, Mathe |
| `rcpsp_algorithm.py` | CPM-Schranken, serielle Konstruktion, Prioritätsregeln, CP-SAT (`AddCumulative`) |
| `rcpsp_scenario.py` | Instanz-Generator (Ketten × Ressourcen, Kapazitäts-/Vorrangdichte-Regler) |
| `rcpsp_constants.py` | Konstanten, Presets |
| `rcpsp_evaluation.py` | Kennzahlen, Sweep, Kapazitäts-/Vorrang-Experimente, Timing-Messreihe |
| `rcpsp_presets.py`, `rcpsp_visualization.py` | Permalink/Presets, Plotly-Figuren (ein Trace je Ressourcen-Slot, achsengesperrt) |
| `tests/` | CP-SAT gegen unabhängiges Job-Shop-Modell (Kollaps-Test), CPM per Handrechnung, Zulässigkeits-Zertifikat, Szenario und Auswertung, Aussagen der App, Presets, AppTest |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
