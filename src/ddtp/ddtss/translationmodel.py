# DDTSS-Django - A Django implementation of the DDTP/DDTSS website
# Copyright (C) 2011 Martijn van Oosterhout <kleptog@svana.org>
# See LICENCE file for details.

import time
from ddtp.database import ddtss

class DefaultTranslationModel(ddtss.TranslationModel):
    """ Stores the model used to determine if a translation is accepted """
    model_name = 'A'

    USER_TYPE_ANONYMOUS = 0
    USER_TYPE_LOGGED_IN = 1
    USER_TYPE_TRUSTED = 2

    def __init__(self):
        """ Sets up a default model """
        self.points = [[0,1],[0,1],[0,1]]
        self.stability_bonus = 1
        self.threshold = 3

    # These functions are only used for the transition, to tweak the default
    # model to include the old settings.  Should not be used in new code
    # since it won't do the right thing.
    def set_threshold(self, threshold):
        self.threshold = threshold

    def set_login_required(self, login_required):
        if login_required:
            self.points[self.USER_TYPE_ANONYMOUS] = [-1,-1]
        else:
            self.points[self.USER_TYPE_ANONYMOUS] = [0,1]

    # These are serialisation and deserialisation to the database. The A is
    # in case we support multiple models in the future.
    def to_string(self):
        return self.model_name + ";".join(",".join(str(p) for p in l) for l in self.points) + "|%d|%d" % (self.stability_bonus, self.threshold)

    @classmethod
    def from_string(cls, s):
        assert s[0] == 'A', 'Expected type A'
        points, stability_bonus, threshold = s[1:].split('|')

        model = cls()
        model.stability_bonus = int(stability_bonus)
        model.threshold = int(threshold)

        # Convert a,b;c,d;e,f -> [[a,b],[c,d],[e,f]]
        model.points = [ [int(p) for p in l.split(',')] for l in points.split(';') ]

        return model

    def to_form_fields(self):
        return dict(ct=self.points[self.USER_TYPE_TRUSTED][self.ACTION_TRANSLATE],
                    lt=self.points[self.USER_TYPE_LOGGED_IN][self.ACTION_TRANSLATE],
                    at=self.points[self.USER_TYPE_ANONYMOUS][self.ACTION_TRANSLATE],
                    cr=self.points[self.USER_TYPE_TRUSTED][self.ACTION_REVIEW],
                    lr=self.points[self.USER_TYPE_LOGGED_IN][self.ACTION_REVIEW],
                    ar=self.points[self.USER_TYPE_ANONYMOUS][self.ACTION_REVIEW],
                    stable=self.stability_bonus,
                    accept=self.threshold)

    def from_form_fields(self, form):
        self.points[self.USER_TYPE_TRUSTED][self.ACTION_TRANSLATE] = form['ct']
        self.points[self.USER_TYPE_LOGGED_IN][self.ACTION_TRANSLATE] = form['lt']
        self.points[self.USER_TYPE_ANONYMOUS][self.ACTION_TRANSLATE] = form['at']
        self.points[self.USER_TYPE_TRUSTED][self.ACTION_REVIEW] = form['cr']
        self.points[self.USER_TYPE_LOGGED_IN][self.ACTION_REVIEW] = form['lr']
        self.points[self.USER_TYPE_ANONYMOUS][self.ACTION_REVIEW] = form['ar']
        self.stability_bonus = form['stable']
        self.threshold = form['accept']

    def map_authority(self, auth_level):
        if auth_level >= ddtss.UserAuthority.AUTH_LEVEL_TRUSTED:
            return self.USER_TYPE_TRUSTED
        return self.USER_TYPE_LOGGED_IN

    def user_allowed(self, user, language, action):
        auth = user.get_authority(language)

        points = self.points[auth.auth_level][action]

        return points >= 0

    def translation_accepted(self, translation):
        # Count points for owner
        if translation.user:
            owner_level = self.map_authority(translation.user.get_authority(translation.language_ref).auth_level)
        else:
            owner_level = self.USER_TYPE_ANONYMOUS

        points = self.points[owner_level][self.ACTION_TRANSLATE]

        # If no reviews, then it can't be accepted
        if len(translation.reviews) == 0:
            return False

        # Count points for reviewers
        for review in translation.reviews:
            if review.user:
                review_level = self.map_authority(review.user.get_authority(translation.language_ref).auth_level)
            else:
                review_level = self.USER_TYPE_ANONYMOUS

            points += self.points[review_level][self.ACTION_REVIEW]

        # Count points for stability bonus
        points += int(self.stability_bonus * (time.time() - translation.lastupdate) / (7*86400))

        return points >= self.threshold

ddtss.TranslationModel.register_model(DefaultTranslationModel)
