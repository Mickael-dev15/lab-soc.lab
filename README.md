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

## Scripts

### analyse_ssh_v3.py
Script Python qui analyse un fichier auth.log (Ubuntu) et produit :
- le nombre d'échecs SSH par IP source ;
- la séparation entre comptes inexistants (énumération) et comptes existants (force brute) ;
- la liste des connexions réussies, avec une alerte quand une IP qui a échoué finit par se connecter.

Testé dans mon lab soc.lab après une attaque simulée depuis Kali (hydra) : le script a détecté la compromission du compte de test « marie ».

Utilisation : `python3 analyse_ssh_v3.py` (avec auth.log dans le même dossier).

