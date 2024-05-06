### Haemosphere Version 5 Documenation

SSH Configuration
-------------
To allow other users to access the instance, add the public key of the user to the authorized_keys in the instance. Once the instance is created, no new pairs of keys could be added to the NECTAR's dasboard and so all the new keys have to be added to the instance via the authorized keys.

To access the authorized keys, 

`cd ~/.ssh`

and then `vi authorized_keys` and add the new public key at the end of the file. That will help provide access to the instance.

