# Runs L1 + L2 + L3 sur les 27 use cases (36 couples dataset × mode)

Généré le 2026-11-26T14:16:00+01:00 par `summarize_use_cases.py`. Tous les chiffres sont recalculés depuis les dossiers `results/use_cases/<DS>/<mode>/` et la ground truth des datasets.

- Code : branche `use-cases-27`, HEAD `a708692` ; scripts `src/agt/**/*.py` identiques à `origin/paul` (`4738a68`) : **True**.
- Exécution : `run_use_cases.py`, scripts Python appelés directement (sans JaCaMo), en séquentiel ; Virtuoso = conteneur Docker `openlinkvirtuoso`, tous les graphes utilisateur vidés avant chaque dataset.
- Statuts : 36/36 runs valides ; L3 : 36 narrations OK, 0 échecs ; dont 7 couples sans aucune alerte L1/L2, pour lesquels le LLM n'est pas appelé (message fixe de `diagnosis_llm.py`).

**Conventions.** P = TP/(TP+FP), fixée à **1** si TP+FP = 0 ; R = TP/(TP+FN), fixée à **1** si TP+FN = 0 ; F1 = 0 si P+R = 0 (convention d'`evaluate_datasets.py`, qui redonne exactement les valeurs de référence). Un couple sans diagnostic attendu ni déclenché vaut donc P = R = F1 = 1 ; un faux positif seul donne P = 0, R = 1, F1 = 0. Micro = TP/FP/FN cumulés ; macro = moyenne des P, R, F1 par couple. L1 : un détecteur compte comme déclenché si son JSON archivé est une liste non vide.

## 1. Les 36 runs

| DS | Mode | Triplets | L2 attendus | L2 déclenchés | TP/FP/FN | F1 | L1+L2 (ms) | Statut | L3 |
|---|---|---:|---|---|---|---:|---:|---|---|
| DS01_clean_baseA | apriori | 170 | — | procedural_unreadiness | 0/1/0 | 0,000 | 22 348 | ok | ok |
| DS01_clean_baseA | aposteriori | 170 | — | — | 0/0/0 | 1,000 | 30 448 | ok | ok |
| DS02_partial_evidence_no_l2_v1 | apriori | 174 | — | procedural_unreadiness | 0/1/0 | 0,000 | 21 504 | ok | ok |
| DS02_partial_evidence_no_l2_v1 | aposteriori | 174 | — | — | 0/0/0 | 1,000 | 17 975 | ok | ok |
| DS03_partial_evidence_no_l2_v2 | apriori | 176 | — | procedural_unreadiness | 0/1/0 | 0,000 | 15 129 | ok | ok |
| DS03_partial_evidence_no_l2_v2 | aposteriori | 176 | — | — | 0/0/0 | 1,000 | 19 957 | ok | ok |
| DS04_structural_fragility_resource_anchor | apriori | 160 | structural_fragility | procedural_unreadiness, structural_fragility | 1/1/0 | 0,667 | 25 639 | ok | ok |
| DS05_critical_service_exposure_basic | apriori | 169 | critical_service_exposure | procedural_unreadiness, structural_fragility | 0/2/1 | 0,000 | 21 233 | ok | ok |
| DS06_critical_service_exposure_concentrated_service | apriori | 164 | critical_service_exposure | procedural_unreadiness, structural_fragility | 0/2/1 | 0,000 | 21 345 | ok | ok |
| DS07_observability_gap_events_and_changes | apriori | 181 ¹ | observability_gap | procedural_unreadiness | 0/1/1 | 0,000 | 8 557 | ok | ok |
| DS08_procedural_unreadiness_basic | apriori | 188 | procedural_unreadiness | procedural_unreadiness | 1/0/0 | 1,000 | 21 055 | ok | ok |
| DS09_functional_mapping_gap_application_chain | apriori | 165 | functional_mapping_gap | functional_mapping_gap, procedural_unreadiness | 1/1/0 | 0,667 | 21 201 | ok | ok |
| DS10_apriori_mixed_two_true_diagnoses | apriori | 164 | critical_service_exposure, functional_mapping_gap | functional_mapping_gap, procedural_unreadiness, structural_fragility | 1/2/1 | 0,400 | 20 962 | ok | ok |
| DS11_single_point_of_failure_basic | aposteriori | 368 | single_point_of_failure | single_point_of_failure | 1/0/0 | 1,000 | 28 922 | ok | ok |
| DS12_change_induced_incident_basic | aposteriori | 378 | change_induced_incident | change_induced_incident | 1/0/0 | 1,000 | 26 437 | ok | ok |
| DS13_service_cascade_basic | aposteriori | 343 | service_cascade | service_cascade | 1/0/0 | 1,000 | 30 488 | ok | ok |
| DS14_traceability_breakdown_basic | aposteriori | 340 | traceability_breakdown | traceability_breakdown | 1/0/0 | 1,000 | 28 283 | ok | ok |
| DS15_unstable_component_basic | aposteriori | 397 | unstable_component | traceability_breakdown | 0/1/1 | 0,000 | 28 522 | ok | ok |
| DS16_application_support_failure_basic | aposteriori | 340 | application_support_failure | — | 0/0/1 | 0,000 | 27 598 | ok | ok |
| DS17_local_infrastructure_cluster_basic | aposteriori | 391 | local_infrastructure_cluster | — | 0/0/1 | 0,000 | 29 305 | ok | ok |
| DS18_aposteriori_mixed_two_true_diagnoses | aposteriori | 398 | service_cascade, unstable_component | service_cascade, traceability_breakdown | 1/1/1 | 0,500 | 29 418 | ok | ok |
| DS19_missing_data_structural_and_temporal | apriori | 337 | — | procedural_unreadiness | 0/1/0 | 0,000 | 22 710 | ok | ok |
| DS19_missing_data_structural_and_temporal | aposteriori | 337 | — | — | 0/0/0 | 1,000 | 28 545 | ok | ok |
| DS20_missing_procedural_links | aposteriori | 338 | traceability_breakdown | traceability_breakdown | 1/0/0 | 1,000 | 28 312 | ok | ok |
| DS21_noisy_irrelevant_events | aposteriori | 279 | — | — | 0/0/0 | 1,000 | 29 763 | ok | ok |
| DS22_noisy_duplicate_and_inconsistent_records | apriori | 276 | — | procedural_unreadiness | 0/1/0 | 0,000 | 20 206 | ok | ok |
| DS22_noisy_duplicate_and_inconsistent_records | aposteriori | 276 | — | — | 0/0/0 | 1,000 | 29 141 | ok | ok |
| DS23_three_diagnoses_ranked_by_urgency | aposteriori | 411 | single_point_of_failure, traceability_breakdown, unstable_component | single_point_of_failure, traceability_breakdown | 2/0/1 | 0,800 | 29 322 | ok | ok |
| DS24_reliability_calibration_bundle | apriori | 253 ¹ | critical_service_exposure, observability_gap, structural_fragility | procedural_unreadiness, structural_fragility | 1/1/2 | 0,400 | 14 179 | ok | ok |
| DS24_reliability_calibration_bundle | aposteriori | 253 ¹ | — | — | 0/0/0 | 1,000 | 16 076 | ok | ok |
| DS25_scalability_small | apriori | 170 | — | procedural_unreadiness | 0/1/0 | 0,000 | 21 488 | ok | ok |
| DS25_scalability_small | aposteriori | 170 | — | — | 0/0/0 | 1,000 | 30 240 | ok | ok |
| DS26_scalability_medium | apriori | 258 | — | procedural_unreadiness | 0/1/0 | 0,000 | 17 502 | ok | ok |
| DS26_scalability_medium | aposteriori | 258 | — | — | 0/0/0 | 1,000 | 28 176 | ok | ok |
| DS27_scalability_large | apriori | 352 | — | procedural_unreadiness | 0/1/0 | 0,000 | 19 719 | ok | ok |
| DS27_scalability_large | aposteriori | 352 | — | — | 0/0/0 | 1,000 | 30 539 | ok | ok |

¹ `dataset.ttl` corrigé le 2026-11-26 (`;` orphelin remplacé par `.`) ; nombre de triplets de référence pris dans `manifest.json` (DS07 : 181, DS24 : 253).

## 2. Agrégats L2

| Périmètre | n | Micro P / R / F1 (TP/FP/FN) | Macro P / R / F1 | Macro, couples avec ≥ 1 attendu (n) |
|---|---:|---|---|---|
| apriori | 16 | 0,217 / 0,455 / 0,294 (5/18/6) | 0,177 / 0,740 / 0,196 | 0,354 / 0,479 / 0,392 (8) |
| aposteriori | 20 | 0,800 / 0,615 / 0,696 (8/2/5) | 0,925 / 0,808 / 0,815 | 0,850 / 0,617 / 0,630 (10) |
| global | 36 | 0,394 / 0,542 / 0,456 (13/20/11) | 0,593 / 0,778 / 0,540 | 0,630 / 0,556 / 0,524 (18) |

**L1 (détecteurs à sortie non vide vs `expected_level1.json`, micro).**

| Périmètre | n | TP / FP / FN | P / R |
|---|---:|---|---|
| apriori | 16 | 44 / 19 / 0 | 0,698 / 1,000 |
| aposteriori | 20 | 24 / 43 / 13 | 0,358 / 0,649 |
| global | 36 | 68 / 62 / 13 | 0,523 / 0,840 |

Détecteurs attendus mais vides (*missed*) et non attendus mais non vides (*extra*), en nombre de couples :

| Mode / détecteur | missed | extra |
|---|---:|---:|
| apriori / procedural/procedure_not_linked_to_resource_type_detector |  | 15 |
| aposteriori / structural/spatial_incident_cluster_detector |  | 10 |
| aposteriori / structural/isolated_incident_resource_detector |  | 9 |
| aposteriori / functional/service_with_repeated_incident_detector |  | 6 |
| aposteriori / functional/module_level_incident_aggregation_detector |  | 5 |
| aposteriori / functional/resource_event_without_service_impact_detector |  | 4 |
| aposteriori / dynamic/event_burst_detector | 3 |  |
| aposteriori / dynamic/flapping_state_detector | 3 |  |
| aposteriori / dynamic/reopened_incident_detector | 3 |  |
| aposteriori / dynamic/stale_incident_detector | 1 | 2 |
| aposteriori / functional/service_impacted_by_multiple_resources_detector |  | 2 |
| aposteriori / procedural/incident_without_ticket_detector |  | 2 |
| aposteriori / procedural/ticket_without_linked_event_detector |  | 2 |
| apriori / structural/orphan_resource_detector |  | 2 |
| aposteriori / dynamic/critical_event_ticket_escalation_detector | 1 |  |
| aposteriori / dynamic/repeated_similar_event_detector | 1 |  |
| aposteriori / functional/service_without_ticket_escalation_detector |  | 1 |
| aposteriori / structural/application_mapping_inconsistency_detector | 1 |  |
| apriori / functional/over_concentrated_service_detector |  | 1 |
| apriori / structural/missing_interface_detector |  | 1 |

## 3. Classement (DS10, DS18, DS23)

| Couple | Classement par priority_score (priorité) | Rang des attendus | Top-1 ∈ attendus | RR |
|---|---|---|---|---:|
| DS10 apriori | 1. structural_fragility (46), 2. functional_mapping_gap (41), 3. procedural_unreadiness (20) | critical_service_exposure: ∅, functional_mapping_gap: 2 | non | 0,500 |
| DS18 aposteriori | 1. service_cascade (75), 2. traceability_breakdown (46) | service_cascade: 1, unstable_component: ∅ | oui | 1,000 |
| DS23 aposteriori | 1. single_point_of_failure (71), 2. traceability_breakdown (46) | single_point_of_failure: 1, traceability_breakdown: 2, unstable_component: ∅ | oui | 1,000 |
| DS24 apriori *(hors périmètre demandé, dataset corrigé)* | 1. structural_fragility (53), 2. procedural_unreadiness (20) | critical_service_exposure: ∅, observability_gap: ∅, structural_fragility: 1 | oui | 1,000 |

**DS10 + DS18 + DS23 : Top-1 = 0,667, MRR = 0,833** (n = 3). Avec DS24 apriori (4 couples à ≥ 2 attendus, périmètre de `kpi_analysis.py`) : Top-1 = 0,750, MRR = 0,875.

DS23, ordre attendu par le manifest : single_point_of_failure > unstable_component > traceability_breakdown ; ordre obtenu : single_point_of_failure > traceability_breakdown ; Top-1 conforme au manifest : **oui**.

## 4. Robustesse (DS19–DS22)

| Couple | Attendus | Déclenchés | TP/FP/FN | F1 | Rapport (tab. 19) |
|---|---|---|---|---:|---:|
| DS19 apriori | — | procedural_unreadiness | 0/1/0 | 0,000 | 1,00 |
| DS19 aposteriori | — | — | 0/0/0 | 1,000 | 1,00 |
| DS20 aposteriori | traceability_breakdown | traceability_breakdown | 1/0/0 | 1,000 | 1,00 |
| DS21 aposteriori | — | — | 0/0/0 | 1,000 | 1,00 |
| DS22 apriori | — | procedural_unreadiness | 0/1/0 | 0,000 | 1,00 |
| DS22 aposteriori | — | — | 0/0/0 | 1,000 | 1,00 |

## 5. Temps d'exécution (DS25–DS27)

| Couple | Triplets | L1 (ms) | L2 (ms) | L1+L2 (ms) | L3 (ms) | ms / script L1 (moy.) | Rapport tab. 20 : L1 / L2 / total (ms) |
|---|---:|---:|---:|---:|---:|---:|---|
| DS25 apriori | 170 | 20 429 | 1 059 | 21 488 | 9 831 | 884 | 4 505 / 254 / 4 759 |
| DS25 aposteriori | 170 | 28 831 | 1 409 | 30 240 | 871 | 925 | 4 505 / 254 / 4 759 |
| DS26 apriori | 258 | 16 496 | 1 006 | 17 502 | 10 774 | 714 | 4 366 / 242 / 4 608 |
| DS26 aposteriori | 258 | 26 833 | 1 342 | 28 176 | 1 010 | 862 | 4 366 / 242 / 4 608 |
| DS27 apriori | 352 | 18 944 | 775 | 19 719 | 7 936 | 819 | 5 823 / 361 / 6 434 |
| DS27 aposteriori | 352 | 29 162 | 1 377 | 30 539 | 1 159 | 937 | 5 823 / 361 / 6 434 |

## 6. Comparaison avec `eval_results.json` (origin/paul) et avec le rapport

### 6.1 Agrégats

« Référence » = recalcul depuis `eval_results.json` (36 couples). « Couples comparables » = les 33 couples valides de ce run dont le dataset n'a pas été modifié : c'est la seule comparaison à périmètre égal. « Ce run (36) » inclut tous les couples valides de ce run.

**Couples non comparables avec la référence du 24/04.** DS07 apriori, DS24 apriori, DS24 aposteriori : leur `dataset.ttl` a été corrigé (`;` orphelin remplacé par `.`). La référence d'`eval_results.json` pour ces couples a été calculée sur des graphes tronqués (DS07 : 162 triplets au lieu de 181, DS24 : 238 triplets au lieu de 253) ; elle n'est donc pas comparable. Ces couples sont exclus des colonnes « couples comparables » et inclus dans la dernière colonne.

| Indicateur | Rapport | Référence (36 couples) | Référence, couples comparables (33) | Ce run, couples comparables (33) | Ce run (36) |
|---|---|---|---|---|---|
| Apriori macro P/R/F1 (tab. 17) | 0,177 / 0,740 / 0,196 | 0,177 / 0,740 / 0,196 | 0,167 / 0,821 / 0,195 | 0,167 / 0,821 / 0,195 | 0,177 / 0,740 / 0,196 |
| Aposteriori macro P/R/F1 (tab. 17) | 0,825 / 0,808 / 0,815 | 0,925 / 0,808 / 0,815 | 0,921 / 0,798 / 0,805 | 0,921 / 0,798 / 0,805 | 0,925 / 0,808 / 0,815 |
| Aposteriori micro P/R/F1 | — | 0,800 / 0,615 / 0,696 | 0,800 / 0,615 / 0,696 | 0,800 / 0,615 / 0,696 | 0,800 / 0,615 / 0,696 |
| Apriori micro P/R/F1 | — | 0,217 / 0,455 / 0,294 | 0,200 / 0,571 / 0,296 | 0,200 / 0,571 / 0,296 | 0,217 / 0,455 / 0,294 |
| Global micro P/R/F1 (tab. 17) | 0,394 / 0,542 / 0,456 | 0,394 / 0,542 / 0,456 | 0,400 / 0,600 / 0,480 | 0,400 / 0,600 / 0,480 | 0,394 / 0,542 / 0,456 |
| Global macro P/R/F1 | — | 0,593 / 0,778 / 0,540 | 0,601 / 0,808 / 0,546 | 0,601 / 0,808 / 0,546 | 0,593 / 0,778 / 0,540 |
| Top-1 / MRR (tab. 18) | 1,000 / 0,833 | — | — | 0,667 / 0,833 (DS10, 18, 23) | 0,667 / 0,833 (DS10, 18, 23) |

### 6.2 Écarts couple par couple avec eval_results.json

Aucun écart : mêmes diagnoseurs déclenchés, mêmes TP/FP/FN et mêmes nombres de triplets sur les 33 couples comparables.

Couples non comparables (dataset corrigé, référence calculée sur un graphe tronqué), à titre indicatif :

| Couple | Référence 24/04 → ce run |
|---|---|
| DS07_observability_gap_events_and_changes apriori | triplets 162 → 181 |
| DS24_reliability_calibration_bundle apriori | triplets 238 → 253 |
| DS24_reliability_calibration_bundle aposteriori | triplets 238 → 253 |

### 6.3 Écarts avec le rapport et explications probables

[V] = vérifié dans les fichiers ; [S] = explication supposée, non vérifiée.

**1. Tableau 17 : le 0,825 du rapport est une coquille.** La référence recalculée depuis `eval_results.json` donne une précision macro aposteriori de 0,925 ; le rappel (0,808) et le F1 (0,815) concordent. [V]

**2. Tableau 17 : à périmètre égal, ce run est identique à la référence.**
- Couple par couple, les 33 couples comparables sont identiques à `eval_results.json` : mêmes diagnoseurs déclenchés, mêmes TP/FP/FN, mêmes triplets (§ 6.2). Leurs agrégats sont donc identiques (colonnes « couples comparables »). [V]
- Les 3 couples non comparables (point 3) donnent aussi les mêmes diagnoseurs déclenchés et les mêmes TP/FP/FN que la référence ; seul le nombre de triplets diffère. Les agrégats sur 36 couples sont donc, eux aussi, égaux à la référence. [V]

**3. DS07 apriori, DS24 apriori et DS24 aposteriori : datasets corrigés, référence non comparable.**
- Leurs `dataset.ttl` contenaient une erreur de syntaxe Turtle : un bloc se terminait par `;` sans le `.` final avant le sujet suivant (DS07 lignes 256 et 264, DS24 ligne 386). [V]
- Le Virtuoso Docker les refusait (`SP029 … syntax error`) : premier passage en `invalid_load`. [V]
- Le 24/04, le Virtuoso Windows 7.2 les avait chargés : 162 et 238 triplets selon `eval_results.json`. [V]
- Correction le 2026-11-26 : les 3 `;` ont été remplacés par `.`, sans autre changement. Les fichiers corrigés chargent **181** et **253** triplets, désormais inscrits dans le champ `triples` de leur `manifest.json` (avec une note dans `README.md`). Le pilote utilise ce champ en priorité sur `eval_results.json`. [V]
- La référence du 24/04 pour ces 3 couples portait donc sur des **graphes tronqués** (162 et 238 triplets) : elle n'est pas comparable, et ces couples sont exclus des colonnes « couples comparables » du § 6.1. [V]
- Pourquoi le Virtuoso 7.2 a accepté un fichier partiel, sans erreur visible : non vérifié. [S]
- Ces 3 couples ont été relancés après les 33 autres, avec `run_use_cases.py` modifié uniquement pour lire `triples` dans le manifest. Le `sha256` du pilote dans leur `run_context.json` diffère donc de celui des 33 autres. [V]

**4. Tableau 18 (Top-1 = 1,000, MRR = 0,833) : le calcul du rapport n'est pas celui défini dans le rapport.**
- Le rapport définit le rang comme « le rang dans la liste triée par score de priorité ».
- Le Top-1 de `kpi_report.json` n'est calculé que sur DS23. Les scores de priorité y valent `"?"` (non lus), donc le « top-1 » est le premier élément de la liste. L'ordre attendu y est SPOF > traceability > unstable, alors que le manifest dit SPOF > unstable > traceability. [V]
- Le MRR de `kpi_report.json` est calculé sur 4 couples (DS10, DS18, DS23, DS24 apriori) dans l'**ordre fixe de la liste de configuration**, pas par `priority_score`. On obtient (1/3 + 1 + 1 + 1)/4 = 0,833. [V]
- Ce run applique la définition du rapport, par `priority_score`, sur DS10, DS18 et DS23 : MRR = (1/2 + 1 + 1)/3 = 0,833. La valeur est la même par coïncidence. [V]
- Top-1 = 0,667 : sur DS10, le premier diagnostic est `structural_fragility` (priorité 46), un faux positif, devant `functional_mapping_gap` (41). [V]
- Sur le périmètre de `kpi_analysis.py` (avec DS24 apriori, dataset corrigé), la définition du rapport donne Top-1 = 0,750 et MRR = 0,875. [V]

**5. Tableau 19 (F1 = 1,00 sur DS19 à DS22) : vrai seulement en mode aposteriori.**
- DS19 et DS22 apriori ont F1 = 0 : `procedural_unreadiness` se déclenche à tort. C'était déjà le cas dans `eval_results.json`. [V]
- Le rapport n'a retenu qu'une ligne par dataset, sans doute celle du mode aposteriori. [S]

**6. Tableau 20 (≈ 4,4 à 6,4 s) : les temps ne sont pas comparables.**
- Ici, les 23 (apriori) ou 31 (aposteriori) scripts L1 tournent en séquentiel, à ≈ 0,7–0,9 s par script : démarrage de l'interpréteur, `import requests`, requête HTTP. D'où 17 à 30 s pour L1+L2. [V]
- Le commentaire de `kpi_analysis.py` montre une mesure séquentielle du même ordre : « 31 agents 18048 ms ». [V]
- Les valeurs du rapport, à une ligne par dataset sans préciser le mode, viennent probablement d'une exécution parallèle des L1 (agents JaCaMo ou `run_all_parallel`). [S]
- Le temps croît peu avec le nombre de triplets (170 → 352) : de 4,8 à 6,4 s dans le rapport, et sans tendance nette ici. Le coût dominant reste le lancement des processus. [V]

**7. Faux positifs apriori : `procedural_unreadiness` se déclenche dans les 14 couples apriori, dont 13 à tort.**
- Il n'est attendu que dans DS08. [V]
- Le détecteur `procedure_not_linked_to_resource_type` est non vide partout : attendu dans DS08, *extra* dans les 13 autres couples. Les bases baseA et baseB contiennent des procédures sans lien vers un type de ressource. [V]
- Le rapport fait le même constat (§ « Exactitude diagnostique globale »).

**8. `unstable_component` n'est jamais déclenché (FN sur DS15, DS18 et DS23).**
- Les trois détecteurs temporels attendus dans ces trois couples (`event_burst`, `flapping_state`, `reopened_incident`) sont vides. [V]
- Ils reposent tous sur des fenêtres `bif:datediff` (5 min, 10 min, 7 jours). La cause est probablement le calcul de ces fenêtres ou le format des timestamps des datasets. [S]
- Les FN de `application_support_failure` (DS16) et de `local_infrastructure_cluster` (DS17) n'ont pas été analysés.

**9. Métrique L1.**
- L'ancien « recall@L1 » d'`evaluate_datasets.py` comptait les codes retour à 0 : il vaut 1,0 sur les 36 couples d'`eval_results.json`. [V]
- La nouvelle mesure, fondée sur les sorties non vides, est nettement plus basse en aposteriori (précision 0,358, rappel 0,649). Elle révèle de nombreux détecteurs non attendus mais non vides (*extra*) et les détecteurs temporels manqués du point 8. [V]

**10. Listing 3 du rapport (§ 6.3) : provenance non traçable.**
- Son texte n'a rien à voir avec la narration mock de `create_demo_outputs.py` (l. 347-357). Le Listing porte sur `RES_TOY_as2` (noria), le mock sur `res_firewall_01` (DS11). [V]
- Aucune sortie brute de ce texte n'existe dans le dépôt ni dans aucune branche. Il n'apparaît que dans `rapport.txt` et `plan_soutenance_detaille.txt`. [V]
- Il a été ajouté le 24/04 (commit `a3d32f0`), alors que le rapport de cette époque ne mentionnait pas encore `diagnosis_llm.py`. [V]
- Il contient un titre et une ligne « Overall severity: CRITICAL ». Or le prompt de production interdit les titres et ne demande pas de sévérité globale. [V]
- Il n'a donc vraisemblablement pas été produit par `diagnosis_llm.py` sous sa forme actuelle. [S]

