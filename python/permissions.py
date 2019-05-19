def has_permission(user_uuid, device_uuid, permission):

    # device_group_name device_group_uuid device_uuid group_permissions

    # TODO: Move this structure to the database after you get it proved out.
    #       Each device belongs to one and only one group.  Each person can be in
    #       0, 1 or more groups.  There are two permissions: organization and group.
    #       Each permission has the permission types: admin and view.
    #
    device_permissions_table = [
            {'device_uuid':'dda50a41-f71a-4b3e-aeea-2b58795d2c99', 'group_id':1234, 'name':'fc1',
             'organization_uuid':'dac952cd-8968-4c26-a508-813861015995',
             'organization':{'admin':True, 'view':True}, 'group':{'admin':False, 'view':True}}]
    person_groups_table = [
            {'person_uuid':'5b108cf5-6e6b-475c-8044-f009b90c1dd0', 'name':'ferguman', 
             'organization_uuid':'dac952cd-8968-4c26-a508-813861015995',
             'group_name':'guest', 'group_id':1234}]
    person_table = [
            {'person_uuid':'4b108cf5-6e6b-475c-8044-f009b90c1dd0', 
             'organization_uuid':'dac952cd-8968-4c26-a508-813861015995'}]

    # Get the device permissions 
    this_devices_permissions = None
    for permissions in device_permissions_table:
        if permissions['device_uuid'] == device_uuid:
            this_devices_permissions = permissions
            break
    
    assert(this_devices_permissions != None), 'error - device has no permissions'

    # Get the person's organization
    user_organization_uuid = None
    for person in person_table:
        if person['person_uuid'] == user_uuid:
            user_organization_uuid = person['organization_uuid']
            break

    assert(user_organization_uuid != None), 'error - user has no organization'

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
