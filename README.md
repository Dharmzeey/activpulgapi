# THIS PROJECT USED A LOT OF RELATED FIELD LOOKUP, SO THERE IS NEED TO GET FAMILIAR WITH THE "related_field" ARGS PASSED IN THE FOREIGNKEY FIELDS SO AS TO MAKE THE VIEWS.PY EASIER TO UNDERSTAND

# CATEGORY AND SUBCATEGORY, for category field on product upload, a request is sent to the 'fetchcategories' endpoint, then after the returned categories can be displayed also, after the subcategories can be queried by passing the id of the category to the endpoint 'fetchsubcategories' which then returns all the subcategories associated with the category id passed, then the id is also saved.

# DELETE REQUEST, for all successful delete, returns a status 204 meaning no content

# the state, location and institution will be saved on the user's FE and any request that can warrant filtering, the state, location and institution will be passed as "st", "lo" and "in" respectively, then the appropriate information will be sent 


# So, when a new state is clicked, it is expected that the location and institution be reseted to load the corresponding location, then when the location is clicked, the institution is reseted to load the associated institution which can then be clicked. 
# E.g when "Lagos state is being saved initially, with "Yaba" as the location and  "Trinity University, Yaba" is the institutiom, and the the user selects "Oyo state" as the new location, it is expected that the Location Yaba and the Institution Trinity University be cleared from the saved cache, and the Places in Oyo state be loaded, the when location in Oyo state is selected, the Institutions are then loaded. 
# Requests should be made to the respective endpoints with the required query parameters to handle the job

# EDIT PRODUCT, when an image is to be edited, the id of the image is sent as a "image_ids_changed" so that the residing image can be edited accurately.
# Also, while user may want to edit their product, they may want to delete or add another image (while not exceeding their max_image) , so the new images uploaded will be sent as "new_images_added", same as "uploaded_images" while the product is being created. But the "uploaded_images" while editing will now serve as placeholder for replacing images.
# That means for edit, If "uploaded_images" is sent, "image_ids_changed" must match with it.

# RECENTLY VIEWED, as the products are being viewed, a list of uuid of the products is being saved locally (local storage on web or mobile as the case may be) then sent to the endpoint when the query is needed 


# Even for the category, when all products have been returned initially and then the user wants to filter by category or subcategory, the FE can just loop through the returned items and do the filter before making another server request

# make purchase will be handled on the FE, where the product, units and neccessary information will be noted and the total will be done and redirected to the vendor's whatsapp