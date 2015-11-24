from django.db import models


class Key(models.Model):
    public_key = models.CharField(max_length=100, unique=True)
    private_key = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return 'Public Key: %s, Private Key: %s' % (
            self.public_key,
            self.private_key,
        )
