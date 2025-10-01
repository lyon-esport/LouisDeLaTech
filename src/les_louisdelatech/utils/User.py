import logging
from datetime import datetime, timezone

import phonenumbers
from typing_extensions import Self
from unidecode import unidecode

from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError

logger = logging.getLogger()


class User:
    def __init__(
        self,
        firstname: str,
        lastname: str,
        birthdate: datetime,
        pseudo: str,
        discord_id: str | None = None,
        email: str | None = None,
        backup_email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        tee_shirt: str | None = None,
        team: str | None = None,
        position: str | None = None,
        is_admin: bool = False,
        is_suspended: bool = False,
    ):
        self.firstname = firstname
        self.lastname = lastname
        self.birthdate = birthdate
        self.pseudo = pseudo
        self.discord_id = discord_id
        self.email = self.email_from_name() if email is None else email
        self.backup_email = backup_email
        self.phone = phone
        self.address = address
        self.tee_shirt = tee_shirt
        self.team = team
        self.position = position
        self.is_admin = is_admin
        self.is_suspended = is_suspended

    def __str__(self) -> str:
        return f"{self.firstname} {self.lastname}"

    def __eq__(self, other: Self):
        return self.email_from_name() == other.email_from_name()

    def __hash__(self):
        return hash((self.firstname, self.lastname))

    def attr_differ(
        self,
        other: Self,
        attr_to_ignore: list[str] = ["_team", "_position", "discord_id", "is_admin"],
    ):
        diffs = []
        for key in filter(
            lambda x: x not in attr_to_ignore,
            self.__dict__.keys(),
        ):
            if getattr(self, key) != getattr(other, key):
                diffs.append(key)
        return diffs

    @classmethod
    def from_hello_asso(cls, order: dict):
        item = None

        for _item in order["items"]:
            if _item["type"] == "Membership" and _item["state"] == "Processed":
                item = {
                    "firstname": order["payer"]["firstName"],
                    "lastname": order["payer"]["lastName"],
                    "backup_email": order["payer"]["email"],
                }

                for custom_field in _item["customFields"]:
                    if "Pseudonyme" == custom_field["name"]:
                        item["pseudo"] = custom_field["answer"]
                    elif "Date de naissance" == custom_field["name"]:
                        try:
                            item["birthdate"] = datetime.strptime(
                                custom_field["answer"], "%d/%m/%Y"
                            ).replace(tzinfo=timezone.utc)
                        except ValueError:
                            raise ValueError(
                                f"User {item['firstname']} {item['lastname']} entered a wrong date of birth"
                            )
                    elif "Adresse postale" == custom_field["name"]:
                        item["address"] = custom_field["answer"]
                    elif "Numéro de téléphone" == custom_field["name"]:
                        item["phone"] = custom_field["answer"]
                    elif "Taille du tee-shirt" == custom_field["name"]:
                        item["tee_shirt"] = custom_field["answer"]
                    # elif (
                    #    "Je m'engage à signer l'engagement de confidentialité"
                    #    in custom_field["name"]
                    # ):
                    #    item["confidentiality"] = custom_field["answer"]
                break

        if item is None:
            raise LouisDeLaTechError(
                f"{order['payer']['firstName']} {order['payer']['lastName']} no valid membership found (or not processed)"
            )
        # elif item["confidentiality"] == "Non":
        #    raise LouisDeLaTechError(
        #        f"{order['payer']['firstName']} {order['payer']['lastName']} disagree to sign the confidentiality agreement"
        #    )

        return cls(
            item["firstname"],
            item["lastname"],
            item["birthdate"],
            item["pseudo"],
            None,
            None,
            item["backup_email"],
            item["phone"],
            item["address"],
            item["tee_shirt"],
            None,
            None,
            False,
            False,
        )

    @classmethod
    def from_google(cls, user: dict):
        """
        :param user: User object from google API
        """
        if not user:
            raise LouisDeLaTechError("User not found, user is not setup on Gsuite")
        elif (
            "customSchemas" not in user
            or "custom" not in user["customSchemas"]
            or "discordId" not in user["customSchemas"]["custom"]
        ):
            raise LouisDeLaTechError(
                f"Discord ID not found, discordId is not setup on Gsuite for user: {user['primaryEmail']}"
            )
        elif (
            "organizations" not in user or "department" not in user["organizations"][0]
        ):
            raise LouisDeLaTechError(
                f"Department not found, department is not setup on Gsuite for user: {user['primaryEmail']}"
            )

        backup_email = None
        if "emails" in user:
            for _email in user["emails"]:
                if "type" in _email and _email["type"] == "home":
                    backup_email = _email["address"]
                    break

        phone = None
        if "phones" in user:
            for _phone in user["phones"]:
                if "type" in _phone and _phone["type"] == "mobile":
                    phone = _phone["value"]
                    break

        address = None
        if "addresses" in user:
            for _address in user["addresses"]:
                if "type" in _address and _address["type"] == "home":
                    address = _address["formatted"]
                    break

        if "organizations" in user and "title" in user["organizations"][0]:
            position = user["organizations"][0]["title"]
        else:
            position = None

        return cls(
            user["name"]["givenName"],
            user["name"]["familyName"],
            datetime.strptime(
                user["customSchemas"]["custom"]["birthdate"], "%d/%m/%Y"
            ).replace(tzinfo=timezone.utc)
            if "birthdate" in user["customSchemas"]["custom"]
            else None,
            user["customSchemas"]["custom"]["pseudo"]
            if "pseudo" in user["customSchemas"]["custom"]
            else None,
            int(user["customSchemas"]["custom"]["discordId"]),
            user["primaryEmail"],
            backup_email,
            phone,
            address,
            user["customSchemas"]["custom"]["teeShirt"]
            if "teeShirt" in user["customSchemas"]["custom"]
            else None,
            user["organizations"][0]["department"],
            position,
            user["isAdmin"],
            user["suspended"],
        )

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, value: str):
        self._firstname = value.title()

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, value: str):
        self._lastname = value.upper()

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value: str):
        self._phone = (
            phonenumbers.format_number(
                phonenumbers.parse(value, "FR"), phonenumbers.PhoneNumberFormat.E164
            )
            if value
            else None
        )

    @property
    def tee_shirt(self):
        return self._tee_shirt

    @tee_shirt.setter
    def tee_shirt(self, value: str):
        if value:
            self._tee_shirt = value.upper()
        else:
            self._tee_shirt = None

    @property
    def team(self):
        return self._team

    @team.setter
    def team(self, value: str):
        if value:
            self._team = value.lower()
        else:
            self._team = None

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value: str):
        if value:
            self._position = value.lower()
        else:
            self._position = None

    @classmethod
    def discord_name(cls, firstname: str, pseudo: str, lastname: str):
        return f"{firstname} {pseudo} {lastname[:1].upper()}"

    def email_from_name(self):
        firstname = unidecode(self.firstname).lower().replace(" ", "").replace("-", "")
        lastname = unidecode(self.lastname).lower().replace(" ", "").replace("-", "")

        return f"{firstname}.{lastname}@lyon-esport.fr"
