from utils.LouisDeLaTechError import LouisDeLaTechError


class User:
    def __init__(self, user):
        """
        :param user: User object from google API
        """
        self.check_user_setup(user)
        self.firstname = user["name"]["givenName"]
        self.lastname = user["name"]["familyName"]
        self.pseudo = user["customSchemas"]["custom"]["pseudo"]
        self.discord_id = user["customSchemas"]["custom"]["discord_id"]
        self.email = user["primaryEmail"]
        self.team = user["organizations"][0]["department"]
        self.role = self.get_role(user)
        self.is_admin = user["isAdmin"]

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
        if not user:
            raise LouisDeLaTechError("User not found, your user is not setup on Gsuite")
        elif "customSchemas" not in user or "custom" not in user["customSchemas"]:
            raise LouisDeLaTechError(
                "Discord ID and Pseudo not found, your discord_id and pseudo are not setup on Gsuite"
            )
        elif "discord_id" not in user["customSchemas"]["custom"]:
            raise LouisDeLaTechError(
                "Discord ID not found, your discord_id is not setup on Gsuite"
            )
        elif "pseudo" not in user["customSchemas"]["custom"]:
            raise LouisDeLaTechError(
                "Pseudo not found, your pseudo is not setup on Gsuite"
            )
        elif (
            "organizations" not in user or "department" not in user["organizations"][0]
        ):
            raise LouisDeLaTechError(
                "Department not found, your department is not setup on Gsuite"
            )
