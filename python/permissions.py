#- def has_permission(user_uuid, device_uuid, permission):

# device_group_name device_group_uuid device_uuid group_permissions

# TODO: Move this structure to the database after you get it proved out.
#       Each device belongs to one and only one group.  Each person can be in
#       0, 1 or more groups.  There are two permissions: organization and group.
#       Each permission has the permission types: admin and view.
#
# TODO: 10/11/2019 - I've hit a situation that this permissions schema does not accomadate. I want
#       to have a food computer that two organizations can both have admin and view rights to
#       and I want to have a third organization that only has view rights to the device.

#TODO: Add group related columns and tables to the fop database to hold the information that is currently hard coded in 
#      in the data structures below.

mars_gid = '30d78ab9-611d-4c44-8bec-a5a91240e1e6'
micds_gid = '09e463e7-cdbf-410c-bc2a-5b0691bffdbf' 
usf_gid = 'b456f6ec-6293-4077-9ad1-f1f1b01524d6' 
slsc_gid = '37cad361-cc28-4730-b676-7a170cf3a37a' 

device_permissions_table = [
    {'device_uuid':'f38dc0c8-658a-4acd-b1c5-c66e17287027', 'group_id':usf_gid, 'name':'usf',
     'organization_uuid':'dac952cd-8968-4c26-a508-813861015995', 'local_name':'fc3',
     'organization':{'admin':True, 'view':True}, 'group':{'admin':False, 'view':False}},
    {'device_uuid':'dda50a41-f71a-4b3e-aeea-2b58795d2c99', 'group_id':usf_gid, 'name':'usf',
     'organization_uuid':'dac952cd-8968-4c26-a508-813861015995', 'local_name':'fc1 camera',
     'organization':{'admin':True, 'view':True}, 'group':{'admin':False, 'view':False}},
    {'device_uuid':'80eb0af1-bb85-41ef-9daf-633279e913bb', 'group_id':mars_gid, 'name':'mars',
     'organization_uuid':'90e22482-087b-484c-8f89-8e88c02164b8', 'local_name':'slsc mvp camera',
     'organization':{'admin':False, 'view':True}, 'group':{'admin':True, 'view':True}},
    {'device_uuid':'25895b2b-3267-45e3-ab25-b1958829d932', 'group_id':micds_gid, 'name':'micds',
     'organization_uuid':'f873cc7f-7ee4-4e88-8357-e308126974ff', 'local_name':'micds_1 camera',
     'organization':{'admin':False, 'view':True}, 'group':{'admin':True, 'view':True}},
    ]

person_groups_table = [
    {'person_uuid':'034a658b-0bce-4214-9276-eebd4b574bf9', 'name':'peter', 
     'organization_uuid':'18ffe759-bf6f-4f34-9a60-7c43d48a7fb0', 'group_name':'mars', 'group_id':mars_gid},
    {'person_uuid':'034a658b-0bce-4214-9276-eebd4b574bf9', 'name':'peter', 
     'organization_uuid':'18ffe759-bf6f-4f34-9a60-7c43d48a7fb0', 'group_name':'micds', 'group_id':micds_gid},
    {'person_uuid':'645f9b8f-ab97-4c81-b8af-d82989812f90', 'name':'paul', 
     'organization_uuid':'f873cc7f-7ee4-4e88-8357-e308126974ff', 'group_name':'micds', 'group_id':micds_gid},
    {'person_uuid':'4b108cf5-6e6b-475c-8044-f009b90c1dd0', 'name':'ferguman', 
     'organization_uuid':'dac952cd-8968-4c26-a508-813861015995', 'group_name':'usf', 'group_id':usf_gid},
    {'person_uuid':'4b108cf5-6e6b-475c-8044-f009b90c1dd0', 'name':'ferguman', 
     'organization_uuid':'dac952cd-8968-4c26-a508-813861015995', 'group_name':'mars', 'group_id':mars_gid},
    {'person_uuid':'4b108cf5-6e6b-475c-8044-f009b90c1dd0', 'name':'ferguman', 
     'organization_uuid':'dac952cd-8968-4c26-a508-813861015995', 'group_name':'micds', 'group_id':micds_gid},
    ]

person_table = [
    {'person_uuid':'645f9b8f-ab97-4c81-b8af-d82989812f90', 
     'organization_uuid':'f873cc7f-7ee4-4e88-8357-e308126974ff'},
    {'person_uuid':'4b108cf5-6e6b-475c-8044-f009b90c1dd0', 
     'organization_uuid':'dac952cd-8968-4c26-a508-813861015995'},
    {'person_uuid':'d2f0fd09-2892-4d35-85c7-c53b0b739b43', 
     'organization_uuid':'90e22482-087b-484c-8f89-8e88c02164b8'},
    {'person_uuid':'034a658b-0bce-4214-9276-eebd4b574bf9', 
     'organization_uuid':'18ffe759-bf6f-4f34-9a60-7c43d48a7fb0'},
    ]


def get_user_groups(user_uuid):
   #- return ('30d78ab9-611d-4c44-8bec-a5a91240e1e6',)

   res = ()
   for group in person_groups_table:
      if group['person_uuid'] == user_uuid:
         res = res + (group['group_id'],)
         #- res.append(group['group_id']) 

   return res


def has_permission(user_uuid, device_uuid, permission):

    # Get the device permissions 
    this_devices_permissions = None
    for permissions in device_permissions_table:
        if permissions['device_uuid'] == device_uuid:
            this_devices_permissions = permissions
            break
    
    assert(this_devices_permissions != None), 'error - device {} has no permissions'.format(device_uuid)

    # Get the person's organization
    user_organization_uuid = None
    for person in person_table:
        if person['person_uuid'] == user_uuid:
            user_organization_uuid = person['organization_uuid']
            break

    assert(user_organization_uuid != None), 'error - user {} has no organization'.format(user_uuid)

    # Does the user have organization permissions
    has_organization_permission = False
    if user_organization_uuid == this_devices_permissions['organization_uuid']:
          has_organization_permission = this_devices_permissions['organization'][permission] 

    # Is the person a member of the device's group
    person_in_device_group = False 
    for group in person_groups_table:
        if user_uuid == group['person_uuid'] and group['group_id'] == this_devices_permissions['group_id']:
            person_in_device_group = True
            break

    # Does the person have group permissions
    has_device_group_permission = False
    if person_in_device_group:
        has_device_group_permission = this_devices_permissions['group'][permission]

    return has_organization_permission or has_device_group_permission 
