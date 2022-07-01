from les_louisdelatech.utils.LouisDeLaTechError import LouisDeLaTechError


class User:
    def __init__(self, user):
        """
        :param user: User object from google API
        """
        print(user)
        self.check_user_setup(user)
        self.firstname = user["name"]["givenName"]
        self.lastname = user["name"]["familyName"]
        self.pseudo = (
            user["customSchemas"]["custom"]["pseudo"]
            if "pseudo" in user["customSchemas"]["custom"]
            else None
        )
        self.discord_id = int(user["customSchemas"]["custom"]["discordId"])
        self.email = user["primaryEmail"]
        self.team = user["organizations"][0]["department"]
        self.role = self.get_role(user)
        self.is_admin = user["isAdmin"]
        self.is_suspended = user["suspended"]

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, value):
        self._firstname = value.lower()

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, value):
        self._lastname = value.lower()

    @property
    def team(self):
        return self._team

    @team.setter
    def team(self, value):
        if value:
            self._team = value.lower()
        else:
            self._team = None

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        if value:
            self._role = value.lower()
        else:
            self._role = None

    @classmethod
    def discord_name(cls, firstname, pseudo, lastname):
        return f"{firstname.title()} {pseudo} {lastname[:1].upper()}"

    @classmethod
    def get_role(cls, user):
        if "organizations" in user and "title" in user["organizations"][0]:
            title = user["organizations"][0]["title"]
        else:
            title = None
        return title

    @classmethod
    def email_from_name(cls, firstname, lastname):
        return f"{firstname}.{lastname}@lyon-esport.fr"

    @classmethod
    def check_user_setup(cls, user):
        print(user)
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
