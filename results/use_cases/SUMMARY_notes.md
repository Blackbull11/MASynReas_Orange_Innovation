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
