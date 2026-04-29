# Comprendre les Modèles de Machine Learning du Projet

> Ce document explique **pourquoi** chaque choix technique a été fait, comment il fonctionne, et ce qu'il apporte au système. Chaque concept est illustré par des exemples concrets tirés du contexte académique.

---

## 0. Le problème à résoudre

Un étudiant arrive sur notre plateforme. Il a validé quelques modules. On lui demande : **"Quel cours devrais-tu faire ensuite ?"**

Naïvement, on pourrait lui montrer tout ce qui est disponible. Mais avec 35 modules, c'est du bruit. Ce qu'on veut, c'est une liste courte, **personnalisée**, de modules pertinents **pour lui spécifiquement** — pas pour un étudiant "moyen".

Il y a deux grandes façons de savoir ce qui est pertinent pour quelqu'un :

1. **Règles logiques** : "Tu as validé Python et Algèbre Linéaire, donc tu peux accéder au Machine Learning." C'est ce que fait le Knowledge Graph.
2. **Comportement de pairs** : "Les étudiants qui ont suivi le même parcours que toi ont ensuite choisi Statistiques Bayésiennes et ont bien réussi." C'est ce que fait le Machine Learning collaboratif.

L'un sans l'autre est insuffisant. D'où l'approche **hybride**.

---

## 1. Le Knowledge Graph — ce qu'il fait, et pourquoi il ne suffit pas

### Ce qu'il fait

Le graphe encode les règles académiques formelles. Il dit :

- Pour suivre le module *Deep Learning*, tu dois maîtriser *Machine Learning* et *Algèbre Linéaire*.
- *Machine Learning* t'enseigne la compétence `sk07`.
- L'étudiant STU042 maîtrise `sk07` et `sk03`.
- Donc, STU042 **peut** suivre *Deep Learning*.

La requête SPARQL vérifie cela automatiquement pour tous les modules. C'est déductif, transparent, et **toujours correct**.

### Pourquoi ça ne suffit pas

Le graphe répond à : **"Peux-tu ?"**. Il ne répond pas à : **"As-tu envie de ? Vas-tu réussir ? Est-ce adapté à ton style ?"**

> **Analogie** : Imagine un bibliothécaire qui connaît ton niveau de français et qui te dit "tu peux lire Proust — tu as le niveau". C'est utile. Mais il ne sait pas que tu détestes la littérature du XIXe siècle et que tu aurais adoré un roman policier de niveau équivalent. Il te manque la connaissance de **tes goûts**.

De plus, si deux étudiants ont exactement le même profil de compétences, le graphe leur recommande exactement les mêmes choses — sans différenciation.

---

## 2. Le Filtrage Collaboratif — l'idée de base

### Le principe

"Les personnes qui ont fait les mêmes choix que toi ont **aussi** aimé X."

C'est la logique derrière les recommandations Netflix, Spotify, Amazon. Ce n'est pas "ce film est objectivement bon", c'est "des gens **comme toi** ont adoré ce film".

> **Analogie** : Tu demandes à cinq amis qui ont le même goût musical que toi ce qu'ils écoutent en ce moment. Tu fais plus confiance à leurs recommandations qu'à un classement général des musiques les plus streamées.

### La matrice des interactions

Pour appliquer cette logique, on construit une **matrice étudiants × modules** :

|        | m01 Python | m07 Algèbre | m10 ML | m21 Deep L. | m22 NLP | m26 Bayes |
|--------|-----------|-------------|--------|-------------|---------|-----------|
| STU001 | ✓ (15/20) | ✓ (17/20)  | ✓ (14/20) | ?       | ?       | ?         |
| STU002 | ✓ (12/20) | ✓ (11/20)  | ✓ (13/20) | ✓ (12/20) | ?    | ?         |
| STU003 | ✓ (18/20) | ✓ (19/20)  | ✓ (17/20) | ✓ (18/20) | ✓ (16/20) | ✓ (17/20) |
| STU042 | ✓ (16/20) | ✓ (15/20)  | ✓ (15/20) | ?       | ?       | ?         |

Les `?` sont les cases vides — les modules que l'étudiant n'a pas encore faits. **Notre objectif est de prédire ces valeurs.**

STU042 ressemble à STU001 et STU003. STU003 a adoré *Deep Learning* (18/20). Donc, on peut prédire que STU042 devrait aussi apprécier *Deep Learning*.

Le problème : cette matrice est **très creuse** (sparse). 100 étudiants × 35 modules = 3 500 cases, mais la plupart sont vides car chaque étudiant n'a suivi que 2 à 6 modules.

---

## 3. SVD — Factorisation de Matrices (la baseline)

### Qu'est-ce que SVD ?

SVD signifie **Singular Value Decomposition** (Décomposition en Valeurs Singulières). C'est une technique mathématique qui décompose une grande matrice en matrices plus petites qui capturent les **facteurs latents** (cachés).

### L'idée intuitive

Au lieu de travailler directement avec la matrice étudiants × modules, on cherche des **profils compressés**.

> **Analogie** : Imagine que tu veuilles décrire le goût musical de 1 000 personnes pour 10 000 chansons. C'est énorme. Mais si tu réalises que tout s'explique avec 5 "dimensions" — goût pour la pop, le jazz, le métal, la variété française, l'électro — tu peux décrire chaque personne avec juste 5 nombres : `[0.9, 0.1, 0.0, 0.4, 0.7]`. Et chaque chanson aussi : `[0.8, 0.0, 0.0, 0.2, 0.6]`. La recommandation devient alors un simple **produit scalaire** entre ces deux vecteurs.

Dans notre contexte, les facteurs latents pourraient représenter des orientations comme :
- "orienté IA / recherche"
- "orienté data engineering"
- "orienté sécurité / réseaux"
- "orienté développement logiciel"
- "orienté mathématiques pures"

Un étudiant n'est conscient d'aucune de ces étiquettes — elles émergent automatiquement des données.

### Formellement

SVD décompose la matrice R (notes) en :

```
R  ≈  U  ×  Σ  ×  Vᵀ
```

- **U** : matrice des étudiants (chaque ligne = vecteur de facteurs latents d'un étudiant)
- **Σ** : matrice diagonale des valeurs singulières (l'importance de chaque facteur latent)
- **Vᵀ** : matrice des modules (chaque colonne = vecteur de facteurs latents d'un module)

Pour prédire la note de l'étudiant `u` pour le module `i` :

```
R̂(u, i) = U[u] · V[i]   (produit scalaire)
```

### Exemple concret

On fixe 3 facteurs latents. Après entraînement :

```
STU042  → [0.8, 0.3, 0.1]   (très orienté "IA", un peu "data", peu "sécurité")
m21 Deep Learning → [0.9, 0.2, 0.0]
m26 Bayes         → [0.7, 0.4, 0.1]
m34 Cybersécurité → [0.1, 0.1, 0.9]
```

Scores prédits :
- Deep Learning : 0.8×0.9 + 0.3×0.2 + 0.1×0.0 = **0.78**
- Bayésien : 0.8×0.7 + 0.3×0.4 + 0.1×0.1 = **0.69**
- Cybersécurité : 0.8×0.1 + 0.3×0.1 + 0.1×0.9 = **0.20**

SVD recommande *Deep Learning* en premier — ce qui est cohérent avec le profil "orienté IA" de STU042.

### Pourquoi SVD comme baseline ?

- Rapide à entraîner.
- Bien documenté, résultats prévisibles.
- Interprétable : on peut inspecter les facteurs latents.
- **Bibliothèque** : `surprise` (Python) implémente SVD avec train/test split intégré.

### Limites de SVD

1. **Linéaire** : SVD suppose que la relation entre un étudiant et un module est un simple produit scalaire. Les interactions complexes (ex: "cet étudiant aime le ML uniquement quand il a déjà fait la théorie des graphes") ne sont pas capturées.
2. **Cold start** : si un nouvel étudiant n'a aucune note, son vecteur `U[u]` ne peut pas être calculé.
3. **Pas de contexte** : SVD ne sait pas que certains modules sont plus difficiles ou ont des prérequis.

C'est pour ça qu'on va au-delà.

---

## 4. Neural Collaborative Filtering (NCF) — la technique avancée

### Pourquoi passer au réseau de neurones ?

SVD suppose que la compatibilité entre un étudiant et un module = produit scalaire de leurs vecteurs. C'est une hypothèse **linéaire**. Or, les préférences humaines sont souvent non-linéaires.

> **Analogie** : SVD est comme dire "les gens qui aiment les mathématiques aiment aussi la physique, proportionnellement". Mais en réalité, un étudiant peut adorer les probabilités **et** détester la théorie de la mesure (pourtant très liée). Ces nuances non-linéaires, SVD ne peut pas les apprendre. Un réseau de neurones, si.

### Architecture NCF

NCF remplace le produit scalaire par un **réseau de neurones** (Multi-Layer Perceptron, MLP) :

```
Étudiant ID ──► [Embedding Layer] ──►─────────┐
                                               ├──► [MLP] ──► [Score prédit]
Module ID ───► [Embedding Layer] ──►─────────┘
```

**Étape 1 — Embedding** : chaque étudiant et chaque module est transformé en un vecteur dense de, disons, 64 dimensions. Ces vecteurs sont appris pendant l'entraînement (similaires aux vecteurs U et V de SVD).

**Étape 2 — Concaténation** : les deux vecteurs sont mis bout à bout en un seul vecteur de 128 dimensions.

**Étape 3 — MLP** : ce grand vecteur passe par plusieurs couches de neurones avec des fonctions d'activation non-linéaires (ReLU). Chaque couche apprend des interactions de plus en plus complexes.

**Étape 4 — Prédiction** : la dernière couche sort un score entre 0 et 1 (probabilité que l'étudiant apprécie ce module).

### Exemple d'interaction non-linéaire capturée par NCF

SVD : `score(STU042, m26_Bayes) = vecteur_étudiant · vecteur_module`

NCF peut apprendre :
- "Si l'étudiant a fait Probabilités ET Algèbre Linéaire → Bayésien est fortement recommandé"
- "Si l'étudiant a fait uniquement Probabilités sans l'Algèbre → Bayésien est moins recommandé même si les skills semblent suffisants"

Cette **interaction conditionnelle** entre plusieurs modules est invisible pour SVD mais visible pour le MLP.

### Pourquoi PyTorch ?

PyTorch est la bibliothèque de référence pour construire des réseaux de neurones sur mesure en Python. Par rapport à TensorFlow, PyTorch est plus flexible pour les architectures expérimentales comme NCF, et son mode "eager execution" facilite le debugging.

### Limites de NCF

- **Besoin de données** : le réseau doit être entraîné sur suffisamment d'interactions. Avec 100 étudiants et 35 modules, c'est léger.
- **Boîte noire** : difficile d'expliquer pourquoi NCF recommande un module spécifique.
- **Cold start** : même problème que SVD — un nouvel étudiant sans historique produit un embedding inutilisable.

→ C'est précisément là qu'intervient le Knowledge Graph.

---

## 5. La Fusion Hybride — pourquoi combiner les deux ?

### Le meilleur des deux mondes

| Critère | Knowledge Graph | SVD / NCF |
|---------|----------------|-----------|
| Cold start (nouvel étudiant) | ✓ Fonctionne | ✗ Échoue |
| Respect des prérequis | ✓ Garanti | ✗ Ignoré |
| Personnalisation fine | ✗ Limitée | ✓ Forte |
| Explicabilité | ✓ Totale | ✗ Faible |
| Découverte de patterns cachés | ✗ Impossible | ✓ Forte |

La fusion combine les deux scores :

```
Score_Final = α × Score_Graphe + β × Score_ML
              avec α + β = 1
```

### Pourquoi la pondération est dynamique

Ce n'est pas un choix arbitraire. La logique est la suivante :

**Étudiant nouveau (0–2 modules complétés) :**
```
α = 0.9, β = 0.1
```
Le ML n'a presque rien à apprendre depuis un si petit historique. On fait confiance au graphe. C'est le **cold start** — le graphe garantit que les recommandations sont au minimum académiquement valides.

**Étudiant intermédiaire (3–6 modules) :**
```
α = 0.6, β = 0.4
```
Le ML commence à avoir un signal. On augmente progressivement son poids.

**Étudiant avancé (7+ modules complétés) :**
```
α = 0.3, β = 0.7
```
Le ML a suffisamment d'historique pour faire des prédictions fiables. La personnalisation prend le dessus, tout en gardant un ancrage graphe (pour ne pas proposer des modules pour lesquels l'étudiant n'a pas les prérequis).

> **Analogie** : Imagine un apprenti cuisinier qui entre dans un restaurant. Les deux premières semaines, le chef lui dit exactement quoi faire (= Knowledge Graph domine). Au bout de 6 mois, le cuisinier connaît les goûts des clients réguliers et commence à improviser intelligemment (= ML prend de l'importance). Le chef ne disparaît jamais — il reste là pour éviter les erreurs de base.

---

## 6. Les métriques d'évaluation — comment savoir si ça marche ?

Une fois le système construit, il faut le mesurer. On utilise des métriques standard de systèmes de recommandation.

### 6.1 Precision@K

**Question** : Sur les K recommandations que j'ai données, combien étaient réellement pertinentes ?

```
Precision@K = (nb de recommandations pertinentes parmi les K premières) / K
```

**Exemple** : on recommande 5 modules à STU042. Il finit par en suivre 3. Mais parmi les 5 recommandés, seulement 2 sont dans les modules qu'il a suivis.
```
Precision@5 = 2/5 = 0.40
```

### 6.2 Recall@K

**Question** : Sur tous les modules pertinents qui existent, combien en ai-je retrouvé dans mes K recommandations ?

```
Recall@K = (nb de recommandations pertinentes parmi les K premières) / (nb total de modules pertinents)
```

**Exemple** : STU042 a suivi 4 modules après usage du système. Nos 5 recommandations en couvraient 2.
```
Recall@5 = 2/4 = 0.50
```

### 6.3 F1-Score

La moyenne harmonique de Precision et Recall. Utile pour trouver un équilibre.

```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
   = 2 × (0.40 × 0.50) / (0.40 + 0.50) = 0.44
```

> **Pourquoi la moyenne harmonique et pas la moyenne simple ?** Parce qu'elle pénalise les déséquilibres. Un système qui recommande tout (Recall = 1.0 mais Precision = 0.01) aurait F1 ≈ 0.02 au lieu de 0.50 avec la moyenne simple — c'est plus honnête.

### 6.4 RMSE et MAE

Ces métriques évaluent l'erreur sur la **prédiction de note** (utile pour la partie SVD/NCF).

**RMSE** (Root Mean Square Error) :
```
RMSE = √( (1/n) × Σ (note_réelle - note_prédite)² )
```

Si STU042 a eu 15/20 en Deep Learning et qu'on avait prédit 13.5 :
```
Erreur = (15 - 13.5)² = 2.25
```
On somme ces erreurs au carré sur tous les exemples, puis on prend la racine. Le carré **punit fort les grandes erreurs**.

**MAE** (Mean Absolute Error) : même idée, mais avec la valeur absolue au lieu du carré — moins sensible aux valeurs aberrantes.

### 6.5 NDCG (Normalized Discounted Cumulative Gain)

**Question** : Est-ce que les modules les plus pertinents sont bien placés **en premier** dans la liste ?

> **Analogie** : Dans une liste de recommandations, trouver le bon module en position 1 est bien plus utile que de le trouver en position 10. NDCG mesure ça.

```
DCG@K = Σ(k=1 à K) [ pertinence(k) / log₂(k+1) ]
```

La pertinence en position 1 est divisée par log₂(2) = 1 (pas de pénalité).
La pertinence en position 5 est divisée par log₂(6) ≈ 2.58 (forte pénalité).

NDCG normalise DCG par le score idéal possible (si on avait parfaitement trié).

**Pourquoi c'est important ici ?** Les étudiants regardent surtout les 3 premières recommandations. Un module pertinent en position 1 a beaucoup plus d'impact qu'en position 8. NDCG capture exactement cette réalité.

---

## 7. Résumé des choix — ce que vous pouvez dire au prof

| Choix | Justification |
|-------|--------------|
| **Knowledge Graph (RDF/OWL + SPARQL)** | Garantit le respect des prérequis académiques. Seule méthode fonctionnelle en cold start. Résultats 100% explicables. |
| **SVD comme baseline** | Méthode éprouvée de filtrage collaboratif, rapide à entraîner, fournit un score de référence pour valider l'approche hybride avant de passer au deep learning. |
| **NCF (Neural Collaborative Filtering)** | Capture des interactions non-linéaires que SVD ne peut pas apprendre (ex : la synergie entre deux modules déjà suivis). PyTorch en facilite l'implémentation et l'expérimentation. |
| **Fusion hybride dynamique** | Ni le graphe ni le ML seul n'est optimal sur tous les profils. La pondération dynamique α/β permet de profiter de la rigueur sémantique du graphe au début, puis de la puissance prédictive du ML quand les données le permettent. |
| **Precision@K, Recall@K, NDCG** | Métriques standard des systèmes de recommandation. NDCG est particulièrement adapté car l'ordre des recommandations compte (un étudiant regarde surtout les premières suggestions). |
| **RMSE/MAE** | Pour évaluer la qualité des prédictions de notes dans la composante SVD/NCF. |

---

## 8. Glossaire rapide

| Terme | En une phrase |
|-------|--------------|
| **Facteur latent** | Une dimension cachée qui résume un pattern dans les données (ex : "orientation IA"). |
| **Embedding** | Un vecteur de nombres réels qui représente un objet (étudiant, module) dans un espace mathématique. |
| **Cold start** | Le problème de recommander à quelqu'un qui n'a aucun historique. |
| **Sparse matrix** | Matrice avec beaucoup de cases vides — typique des interactions utilisateur-item. |
| **ReLU** | Fonction d'activation des neurones : `f(x) = max(0, x)`. Introduit la non-linéarité. |
| **Produit scalaire** | `[a, b, c] · [x, y, z] = ax + by + cz`. Mesure la similarité entre deux vecteurs. |
| **OWL-RL** | Sous-ensemble du langage OWL permettant un raisonnement automatique sur le graphe (inférer de nouveaux triplets à partir des règles). |
| **SPARQL** | Langage de requêtes pour les graphes RDF, analogue au SQL pour les bases relationnelles. |
