# Chapitre 1 : Installation et Premier Démarrage

Bienvenue dans ClientDocManager ! Ce chapitre vous guidera à travers les étapes nécessaires pour installer l'application sur votre ordinateur et la démarrer pour la première fois.

## 1.1. Prérequis Système

Avant d'installer ClientDocManager, assurez-vous que votre ordinateur dispose de :

*   **Système d'exploitation compatible**:
    *   Windows (Windows 10 ou plus récent recommandé)
    *   macOS
    *   Linux
    *(La compatibilité exacte peut dépendre de la version spécifique de l'application que vous installez).*
*   **Python 3.x**: Si vous installez à partir des sources, Python (version 3.7 ou plus récente) doit être installé. Pour une version packagée de l'application (ex: un `.exe` ou `.dmg`), Python n'est généralement pas un prérequis direct pour l'utilisateur.
*   **Espace disque suffisant**: Pour l'application elle-même et pour les données et documents que vous allez gérer.
*   **Permissions d'installation**: Vous pourriez avoir besoin de droits d'administrateur pour installer l'application, selon la méthode d'installation et la configuration de votre système.

## 1.2. Méthodes d'Installation

Il peut exister plusieurs manières d'installer ClientDocManager, en fonction de la manière dont elle vous est fournie :

### Méthode A : Utilisation d'un Programme d'Installation (Recommandé pour la plupart des utilisateurs)

Si vous avez reçu un fichier d'installation (par exemple, `ClientDocManager_Setup.exe` pour Windows, `ClientDocManager.dmg` pour macOS, ou un paquet `.deb`/`.rpm` pour Linux) :

1.  **Téléchargez** le fichier d'installation fourni par votre administrateur ou depuis la source officielle.
2.  **Exécutez le fichier d'installation** :
    *   **Windows**: Double-cliquez sur le fichier `.exe` et suivez les instructions à l'écran. Vous pourriez être invité à accepter les termes d'une licence, à choisir un dossier d'installation, et à décider si vous voulez créer des raccourcis.
    *   **macOS**: Double-cliquez sur le fichier `.dmg` pour l'ouvrir. Faites ensuite glisser l'icône de l'application ClientDocManager dans votre dossier "Applications".
    *   **Linux**: La méthode dépendra du type de paquet. Pour un `.deb` (Debian/Ubuntu), vous pouvez souvent l'installer en double-cliquant ou via la commande `sudo dpkg -i ClientDocManager.deb` (suivie de `sudo apt-get install -f` si des dépendances sont manquantes). Pour un `.rpm` (Fedora/RedHat), la commande serait `sudo rpm -ivh ClientDocManager.rpm`.
3.  Une fois l'installation terminée, vous devriez trouver ClientDocManager dans votre liste de programmes ou d'applications, et un raccourci a pu être créé sur votre bureau.

### Méthode B : Installation à partir des Sources (Pour utilisateurs avancés ou développeurs)

Cette méthode est plus technique et est généralement utilisée si vous avez accès au code source de l'application. Elle est brièvement décrite ici à titre informatif et est détaillée dans le `README.md` principal du projet.

1.  **Cloner ou télécharger le code source**.
2.  **Créer un environnement virtuel Python** (recommandé).
3.  **Installer les dépendances** listées dans le fichier `requirements.txt` en utilisant `pip install -r requirements.txt`.
4.  **Lancer l'application** avec `python main.py`.

**Note pour les utilisateurs finaux**: Si vous n'êtes pas sûr de la méthode à utiliser, demandez à votre administrateur système ou à la personne qui vous a fourni l'application. La Méthode A est généralement celle attendue.

## 1.3. Premier Démarrage de l'Application

1.  **Lancez ClientDocManager**:
    *   Utilisez le raccourci sur votre bureau ou dans votre menu Démarrer/Launchpad.
    *   Si installé depuis les sources, exécutez `python main.py` depuis le dossier de l'application dans votre environnement virtuel activé.

2.  **Écran de Démarrage (Splash Screen)**: Une image de démarrage peut s'afficher brièvement pendant que l'application charge.

3.  **Configuration Initiale (Si c'est la toute première fois sur cet ordinateur)**:
    *   Il est possible qu'un dialogue de **Configuration Initiale** apparaisse. Ce dialogue vous demandera de confirmer ou de définir certains paramètres de base, comme :
        *   La création des informations de votre entreprise (Nom, Adresse, etc.).
        *   Les emplacements des dossiers pour les modèles de documents et les fichiers clients (ces dossiers peuvent être créés automatiquement pour vous).
    *   Suivez attentivement les instructions de ce dialogue. Ces informations sont importantes pour le bon fonctionnement de l'application.

4.  **Dialogue de Connexion**:
    *   Une fois la configuration initiale terminée (si elle était nécessaire), le dialogue de **Connexion** s'affichera.
    *   Vous devrez saisir le **Nom d'utilisateur** et le **Mot de passe** qui vous ont été fournis par votre administrateur.
    *   **Option "Se souvenir de moi"**: Si vous cochez cette case, l'application pourra se souvenir de votre nom d'utilisateur pour faciliter les prochaines connexions, voire vous connecter automatiquement (selon la configuration).
    *   Cliquez sur **OK** pour vous connecter.

5.  **Fenêtre Principale**: Si vos identifiants sont corrects, la fenêtre principale de ClientDocManager (appelée `DocumentManager`) s'ouvrira, et vous serez prêt à utiliser l'application !

## 1.4. En Cas de Problèmes au Premier Démarrage

*   **Identifiants incorrects**: Vérifiez attentivement votre nom d'utilisateur et votre mot de passe. Respectez la casse (majuscules/minuscules). Si vous avez oublié vos identifiants, contactez votre administrateur.
*   **Problèmes de base de données**: Si l'application signale une erreur de base de données, il est possible que la configuration initiale n'ait pas pu créer correctement le fichier de base de données. Assurez-vous que l'application a les droits d'écriture nécessaires dans son dossier de configuration (souvent dans votre profil utilisateur). Contactez votre support technique si le problème persiste.
*   **Polices manquantes**: L'application utilise certaines polices pour la génération de documents PDF. Si des messages d'erreur concernant des polices manquantes apparaissent (surtout lors de la génération de PDF), informez-en votre administrateur. Les polices nécessaires (comme Arial, Showcard Gothic) doivent normalement être installées avec l'application ou sur votre système. (Voir la section "Fonts" du `README.md` principal pour plus de détails techniques).

Vous êtes maintenant prêt à explorer les fonctionnalités de ClientDocManager ! Référez-vous aux chapitres suivants de ce manuel pour apprendre à utiliser les différents modules.
