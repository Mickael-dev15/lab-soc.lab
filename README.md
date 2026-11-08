# Lab SOC personnel : soc.lab

Je suis Patrick Kassi, ingénieur support, réseaux et systèmes, avec plus de 11 ans d'expérience en Afrique de l'Ouest et centrale. Je me forme au métier d'analyste SOC, et ce dépôt est mon carnet de bord.

J'y documente un lab construit de zéro, des attaques que je simule moi-même, la façon dont je les détecte, et les erreurs que je rencontre en chemin. Chaque incident est décrit avec son symptôme, sa cause, la correction et la leçon retenue.

Certifications : CompTIA Security+ (SY0-701), Cisco CCNA (200-301), AWS Cloud Practitioner.

## Architecture du lab

Réseau isolé sous VMware Workstation, découpé en trois zones filtrées par un pare-feu.

| Machine | Système | Zone | Adresse | Rôle |
|---|---|---|---|---|
| FW01 | OPNsense 26.7 | toutes | 10.10.x.254 | Pare-feu, routage entre les zones, journalisation |
| SIEM01 | Ubuntu Server 24.04 | Serveurs | 10.10.10.10 | Wazuh 4.14 (collecte, détection, tableau de bord) |
| DC01 | Windows Server 2025 | Serveurs | 10.10.10.11 | Contrôleur de domaine soc.lab, DNS |
| SRV01 | Ubuntu Server 24.04 | Serveurs | 10.10.10.20 | Serveur Linux cible (SSH) |
| WS01 | Windows 11 Entreprise | Postes | 10.10.20.10 | Poste du domaine, Sysmon et agent Wazuh |
| KALI01 | Kali Linux | Attaquant | 10.10.99.10 | Simulation d'attaques |

La zone Attaquant n'a aucun accès sortant. Seuls les flux nécessaires à chaque scénario sont ouverts, et toutes les règles concernées sont journalisées.

## Compétences mises en œuvre

- **Réseau et filtrage** : segmentation, règles OPNsense, alias, journaux du pare-feu, analyse de trafic avec Wireshark
- **SIEM** : déploiement de Wazuh, agents Windows et Linux, lecture et tri des alertes, requêtes DQL
- **Windows** : Active Directory, journaux de sécurité (4624, 4625, 4688…), Sysmon avec la configuration sysmon-modular
- **Linux** : auth.log, journald, analyse en ligne de commande (grep, awk, sort, uniq)
- **Python** : scripts d'analyse de journaux (détection de force brute et de compromission)
- **Méthode** : MITRE ATT&CK, diagnostic couche par couche, rédaction de rapports d'incident

## Scénarios réalisés

| Date | Scénario | Technique MITRE | Résultat |
|---|---|---|---|
| 30/10/2026 | Force brute RDP sur WS01 depuis Kali | T1110.001 | Compromission détectée dans Wazuh (règles 60122, 60204, 92652) |
| 03/11/2026 | Énumération et force brute SSH sur SRV01 | T1110.001 | Compromission du compte de test détectée dans auth.log et par script Python |

## Contenu du dépôt

- `README.md` : ce journal, séance par séance
- `scripts/` : mes scripts d'analyse

---

# Journal du lab soc.lab

## S1 · Mardi 20/10/2026 · Mise en route de FW01 (OPNsense 26.7)

### Plan d'adressage

| Interface | Zone | Adresse |
|---|---|---|
| WAN (em0) | NAT VMware | DHCP (192.168.47.145/24) |
| LAN (em1) | Serveurs, VMnet2 | 10.10.10.254/24 |
| OPT1 (em2) | Postes, SOC-POSTES | 10.10.20.254/24 |
| OPT2 (em3) | Attaquant, SOC-ATTAQUANT | 10.10.99.254/24 |

### Incidents rencontrés

**1. Impossible de lancer l'installation**
- Symptôme : "Login incorrect" en boucle sur la console.
- Cause : je me connectais avec root, qui démarre le mode live. Le compte d'installation est installer.
- Correction : connexion avec installer / opnsense, puis clavier passé en AZERTY dans l'installateur.
- Leçon : lire le message d'accueil de la console, il donnait la réponse.

**2. Adresse LAN posée sur la mauvaise interface**
- Symptôme : 10.10.10.254 apparaissait sur OPT1 (em2) au lieu de LAN (em1).
- Cause : mauvais numéro choisi dans la liste de l'option 2.
- Correction : OPT1 passé en 10.10.20.254, puis LAN en 10.10.10.254.
- Leçon : toujours relire l'en-tête de la console après une modification.

**3. Interface web injoignable depuis mon PC**
- Symptôme : ping 10.10.10.254 → "Réponse de 10.10.10.1 : Impossible de joindre l'hôte de destination".
- Cause : adaptateurs 3 et 4 inversés dans VMware, em1 n'était pas sur VMnet2. Problème de couche 2 (ARP sans réponse), pas de filtrage.
- Correction : adaptateurs remis dans le bon ordre, en vérifiant les adresses MAC.
- Leçon : "hôte injoignable" renvoyé par ma propre IP = problème de câblage, pas de pare-feu.

**4. Mauvais fuseau horaire**
- Symptôme : la console affichait 18:05 -01 au lieu de 20:05.
- Cause : Etc/GMT+1 choisi, ce qui correspond à UTC-1 (signe inversé en POSIX).
- Correction : fuseau Africa/Douala (WAT, UTC+1).
- Leçon : des horodatages faux rendent la chronologie d'un incident inutilisable.

### État final
FW01 opérationnel, interface web accessible depuis https://10.10.10.254, snapshot FW01-base-OK pris.

## S1 (suite) · 24 et 25/10/2026 · Wireshark et mise en route de SIEM01 (Wazuh 4.14)

### Ce que j'ai fait
- Capture Wireshark sur VMnet2 : requête et réponse ARP, poignée de main TCP complète vers FW01, Client Hello TLS 1.3.
- Installation de SIEM01 (Ubuntu Server 24.04, 10.10.10.10) puis de Wazuh en mode tout-en-un.

### Incidents rencontrés

**1. Disque de SIEM01 à moitié utilisé**
- Symptôme : la partition / ne faisait que 49 Go sur un disque de 100 Go.
- Cause : par défaut, l'installateur Ubuntu n'alloue que la moitié du groupe LVM.
- Correction : volume ubuntu-lv porté au maximum pendant l'installation.
- Leçon : un SIEM se remplit vite, l'espace disque se vérifie dès l'installation.

**2. Mes commandes sudo absentes de Wazuh**
- Symptôme : aucune alerte sudo dans Wazuh, alors que les commandes figurent dans auth.log.
- Cause : ces commandes ont été lancées avant que Wazuh ne commence à collecter.
- Correction : nouvel événement généré après l'installation, alertes 5402 et 5403 bien reçues.
- Leçon : un SIEM ne voit que ce qu'il collecte, et à partir du moment où il collecte. Absence de preuve n'est pas preuve d'absence.

**3. Deux fuseaux horaires dans le même auth.log**
- Symptôme : certaines lignes en +00:00, d'autres en +01:00.
- Cause : le changement de fuseau n'a été pris en compte qu'au redémarrage.
- Leçon : toujours lire le décalage horaire d'un horodatage avant de construire une chronologie.

---

## S2 · 27 au 30/10/2026 · Active Directory, poste du domaine et premier scénario d'attaque

### Ce que j'ai fait
- DC01 (Windows Server 2025) promu contrôleur du domaine soc.lab, avec redirecteur DNS vers FW01.
- Règle de pare-feu pour la zone Postes, avec source limitée à POSTES network et journalisation.
- WS01 (Windows 11 Entreprise) joint au domaine, Sysmon installé avec la configuration sysmon-modular, agent Wazuh déployé et branché sur le journal Sysmon.
- KALI01 installé dans la zone Attaquant, avec un seul flux ouvert : RDP vers WS01.

### Incidents rencontrés

**1. Deux commandes PowerShell fusionnées**
- Symptôme : erreur « paramètre spécifié plusieurs fois » sur New-NetIPAddress.
- Cause : le retour à la ligne avait disparu au copier-coller.
- Correction : commandes relancées une par une.
- Leçon : relire une ligne collée avant de l'exécuter.

**2. Mot de passe DSRM exposé**
- Symptôme : la promotion du DC échouait sur la complexité du mot de passe.
- Cause : j'avais écrit le mot de passe à la place du texte de l'invite Read-Host. Il apparaissait donc en clair à l'écran et dans l'historique PowerShell, et le mot de passe réellement envoyé était vide.
- Correction : historique supprimé, nouveau mot de passe saisi à l'invite.
- Leçon : un mot de passe en clair dans un historique est une technique d'attaque connue (MITRE T1552.001). Read-Host -AsSecureString existe pour l'éviter.

**3. Le port RDP de WS01 apparaissait « filtered »**
- Symptôme : nmap depuis KALI01 ne recevait aucune réponse sur le port 3389.
- Diagnostic : le service RDP écoutait bien sur WS01. Le journal en direct d'OPNsense montrait le paquet bloqué par la règle par défaut.
- Cause : la règle et l'alias WS01 n'étaient pas encore appliqués. En vérifiant, j'ai aussi trouvé le réseau attaquant ajouté par erreur dans l'alias.
- Correction : alias nettoyé, modifications appliquées, port vu « open ».
- Leçon : « filtered » veut dire qu'un pare-feu jette le paquet. On prouve lequel avec ses journaux avant de modifier quoi que ce soit.

**4. Fichier de configuration Sysmon introuvable (erreur 404)**
- Cause : le fichier sysmonconfig.xml n'est plus dans le dépôt sysmon-modular, il est publié dans les Releases.
- Leçon : un 404 prouve que le réseau fonctionne. C'est la ressource qui n'existe pas à cette adresse.

### Scénario : force brute RDP sur WS01 (30/10/2026, vers 13h20 WAT)
- Attaque : liste de mots de passe testée avec NetExec contre le compte de test j.dupont, depuis 10.10.99.10. Le mot de passe, volontairement faible, était dans la liste.
- Détection dans Wazuh : série d'événements 4625 (règle 60122) avec subStatus 0xC000006A, donc compte existant et mauvais mot de passe, puis corrélation de niveau 10 (règle 60204), puis connexion réussie 4624 (règle 92652).
- Logon Type 3 et non 10 : avec le NLA, le mot de passe est vérifié au niveau réseau avant l'ouverture de la session graphique.
- La règle 92652 évoque un possible pass-the-hash à cause de l'authentification NTLM. Ici, il s'agit d'un mot de passe deviné : la règle doit être requalifiée par l'analyste.
- Facteur aggravant : seuil de verrouillage des comptes à 0, donc essais illimités.
- Résultat : **compte compromis**. Technique MITRE T1110.001 (Password Guessing).
- Recommandations : réinitialiser le mot de passe et fermer les sessions du compte, rechercher l'activité après compromission, activer le verrouillage des comptes, placer le RDP derrière un VPN avec MFA.

**Mon erreur d'analyse**
- Dans mon premier rapport, j'ai conclu que l'attaque avait échoué, alors que la connexion réussie était visible.
- Leçon : chercher systématiquement l'événement de succès avant de conclure. Un faux négatif laisse un compte compromis en service.

---

## S3 · 03 au 08/11/2026 · Linux, attaque SSH et premiers scripts Python

### Ce que j'ai fait
- SRV01 (Ubuntu Server 24.04, 10.10.10.20) installé comme cible Linux, avec un compte de test volontairement faible.
- Flux SSH ouvert depuis la zone Attaquant vers SRV01 uniquement, règle journalisée.
- Agent Wazuh sur SRV01, alimenté par journald.
- Trois versions d'un script Python d'analyse d'auth.log (dossier scripts).

### Incidents rencontrés

**1. SRV01 branché sur le mauvais réseau**
- Symptôme : pendant l'installation, la carte recevait une adresse 192.168.47.x par DHCP.
- Cause : carte réseau en NAT au lieu de VMnet2, qui n'a pas de DHCP.
- Correction : carte passée sur VMnet2, adresse fixe 10.10.10.20.
- Leçon : une adresse inattendue révèle par où passe réellement le trafic.

**2. Port SSH « closed »**
- Symptôme : nmap affichait 22/tcp closed.
- Cause : OpenSSH n'était pas installé sur SRV01.
- Correction : installation et activation du service.
- Leçon : « closed » veut dire que la machine a répondu par un RST. Le réseau et le pare-feu fonctionnent, c'est le service qui manque.

**3. Faux positifs dans mon analyse**
- Symptôme : mes propres commandes sudo apparaissaient comme des échecs SSH.
- Cause : sudo enregistre le texte des commandes, qui contenait « Failed password ».
- Correction : double condition dans le script (sshd et Failed password).
- Leçon : l'enquête laisse ses propres traces dans les journaux, il faut les filtrer.

### Scénario : énumération et force brute SSH sur SRV01 (03/11/2026)
- Attaque : hydra depuis 10.10.99.10, avec 6 comptes et 5 mots de passe.
- Résultat de l'analyse : 29 échecs depuis 10.10.99.10. Comptes inexistants visés : admin, test, oracle. Comptes existants visés : root, ubuntu, marie.
- Connexion réussie du compte marie le 03/11/2026 à 19:58:36 (+01:00) : **compte compromis**. Technique MITRE T1110.001.
- Le compte ubuntu a résisté parce que son mot de passe n'était pas dans la liste. Avec un mot de passe faible, l'attaquant aurait obtenu les droits sudo, donc un accès root.
- Au moment de l'attaque, SRV01 n'avait pas d'agent Wazuh : l'attaque n'existait que dans auth.log. Angle mort corrigé le 05/11.

### Scripts Python
- v1 : échecs SSH par IP source, triés.
- v2 : séparation des comptes inexistants (énumération) et existants (force brute).
- v3 : connexions réussies et alerte quand une IP qui a échoué finit par se connecter.
- Ce que j'ai appris en route : un bug peut produire un résultat plausible mais faux sans aucun message d'erreur. Je vérifie maintenant chaque résultat avec un calcul attendu, et je fais extraire les valeurs par le script plutôt que de les écrire en dur.

---

## Scripts

### analyse_ssh_v3.py
Script Python qui analyse un fichier auth.log (Ubuntu) et produit :
- le nombre d'échecs SSH par IP source ;
- la séparation entre comptes inexistants (énumération) et comptes existants (force brute) ;
- la liste des connexions réussies, avec une alerte quand une IP qui a échoué finit par se connecter.

Testé dans mon lab soc.lab après une attaque simulée depuis Kali (hydra) : le script a détecté la compromission du compte de test « marie ».

Utilisation : `python3 analyse_ssh_v3.py` (avec auth.log dans le même dossier).

