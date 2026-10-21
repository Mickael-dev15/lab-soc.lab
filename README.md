# lab-soc.lab
Roodmap Cybersécurité
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
