describe("Laser Job", function() {

    beforeEach(function() {
        cy.fixture('test-data').then(function(testData){
            this.testData = testData});
    });

    beforeEach(function() {
        cy.visit(this.testData.url_laser);
        cy.wait(10000);
        cy.loginLaser(this.testData.email, this.testData.password);
        cy.visit(this.testData.url_laser);
        cy.wait(5000);
    });

    it('Add design', function() {
       cy.get('[id="working_area_tab_file_btn"]').click();
       cy.get('.files_template_model_svg').first().click();
       cy.wait(3000);
       cy.get('.rotation').clear().type('-90.5 {enter}');
       cy.get('.vertical').clear().type('356.1 {enter}');
       cy.get('.horizontal').clear().type('61.2 {enter}');
       cy.get('.translation').clear().type('16.3, 11.3 {enter}');
       cy.get('[id="laser_button"]').click();
       cy.get('[id="laserhead_focus_reminder_modal"]').find('.btn').first().click();
       cy.get('[id="laser_button"]').click();
       cy.get('.material_entry').contains('Cardboard, single wave').click();
       // cy.get('[id="material_color_8b624a"]').click();
       cy.wait(1000);
       cy.get('[id="material_thickness_1.5"]').click();
       cy.get('[id="svgtogcode_img_intensity_black"]').clear().type('95');
       cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type('1500');
       cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
       cy.get('.passes_input').first().clear().type('4');
       cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type('8');
       cy.get('[id="svgtogcode_img_line_dist"]').clear().type('1');
       cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick({force:true});
       cy.get('[id="start_job_btn"]').dblclick();
       cy.wait(2000);
       cy.get('.alert-success').should('to.exist', 'Preparation done');
       cy.reload();
       cy.wait(10000);
       cy.get('[id="designlib_tab_btn"]').click();
       cy.get('[id="design_lib_filter_gcode_radio"]').click();
       cy.get('.files_template_machinecode_gcode').first().click();
       cy.get('[id="laser_button"]').click();
       cy.get('[id="laserhead_focus_reminder_modal"]').find('.btn').first().click();
       cy.logout();
    });

    it('Add texts', function() {
       cy.wait(3000);
       cy.get('[id="working_area_tab_text_btn"]').click();
       cy.get('[id="quick_text_dialog_text_input"]').type('project owner');
       cy.get('[id="quick_text_cw"]').click();
       cy.get('[id="quick_text_dialog_circle"]').trigger('right');
       cy.get('.quicktext-font-button').last().click();
       cy.get('[id="quick_text_stroke"]').click();
       cy.get('[id="quick_text_text_done_btn"]').click();
       cy.get('.translation').clear().type('140.0, 138.0');
       cy.get('.rotation').clear().type('-50.5');
       cy.get('.horizontal').clear().type('116.3 mm');
       cy.get('.vertical').clear().type('132.3 mm');
        // string 2
       cy.get('[id="working_area_tab_text_btn"]').click();
       cy.get('[id="quick_text_dialog_text_input"]').type('e2e tester');
       cy.get('[id="quick_text_ccw"]').click();
       cy.get('[id="quick_text_dialog_circle"]').trigger('right');
       cy.get('[id="quick_text_fill"]').click();
       cy.get('[id="quick_text_text_done_btn"]').click();
       cy.get('.translation').eq(1).clear().type('223.0, 235.0');
       cy.get('.rotation').eq(1).clear().type('90.5');
       cy.get('.horizontal').eq(1).clear().type('115.3 mm');
       cy.get('.vertical').eq(1).clear().type('110.3 mm');
        // string 3
       cy.get('[id="working_area_tab_text_btn"]').click();
       cy.get('[id="quick_text_dialog_text_input"]').type('unit tester');
       cy.get('[id="quick_text_straight"]').click();
       cy.get('[id="quick_text_text_done_btn"]').click();
       cy.get('.translation').eq(2).clear().type('235.0, 138.0');
       cy.get('.rotation').eq(2).clear().type('-50.5');
       cy.get('.horizontal').eq(2).clear().type('125.3 mm');
       cy.get('.vertical').eq(2).clear().type('130.3 mm');

       cy.get('[id="laser_button"]').click();
       cy.get('[id="laserhead_focus_reminder_modal"]').find('.btn').first().click();
       cy.get('[id="laser_button"]').click();
       cy.get('.material_entry').contains('Cardboard, single wave').click({force:true});
       // cy.get('[id="material_color_8b624a"]').click();
       cy.wait(1000);
       cy.get('[id="material_thickness_1.5"]').click();
       cy.get('[id="svgtogcode_img_intensity_black"]').clear().type('70');
       cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type('3000');
       cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
       cy.get('.passes_input').first().clear().type('1');
       cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type('2');
       cy.get('[id="svgtogcode_img_line_dist"]').clear().type('1');
       cy.get('[id="parameter_assignment_engraving_mode_basic_btn"]').dblclick({force:true});
       cy.get('[id="start_job_btn"]').dblclick();
       cy.get('.alert-success').should('to.exist', 'Preparation done');
       cy.reload();
       cy.wait(10000);
       cy.get('[id="designlib_tab_btn"]').click();
       cy.get('[id="design_lib_filter_gcode_radio"]').click();
       cy.get('.files_template_machinecode_gcode').first().click();
       cy.get('[id="laser_button"]').click();
       cy.get('[id="laserhead_focus_reminder_modal"]').find('.btn').first().click();
       cy.logout();
    });

    it('Add shapes', function() {
       cy.get('[id="working_area_tab_shape_btn"]').click();
       cy.get('[id="shape_tab_link_heart"]').click();
       cy.get('[id="quick_shape_heart_w"]').clear().type('60');
       cy.get('[id="quick_shape_heart_h"]').clear().type('80');
       cy.get('[id="quick_shape_fill"]').click();
       cy.get('[id="quick_shape_stroke"]').click();
       cy.get('[id="quick_shape_shape_done_btn"]').click();
       cy.get('.translation').clear().type('35.0, 38.0');
       cy.get('.rotation').clear().type('50.5');
       cy.get('.horizontal').clear().type('160.3 mm');
       cy.get('.vertical').clear().type('89.3 mm');
        // shapes 2
       cy.get('[id="working_area_tab_shape_btn"]').click();
       cy.get('[id="shape_tab_link_circle"]').click();
       cy.get('[id="quick_shape_circle_radius"]').clear().type('60');
       cy.get('[id="quick_shape_fill"]').click();
       cy.get('[id="quick_shape_shape_done_btn"]').click();
       cy.get('.translation').eq(1).clear().type('200.0, 38.0');
       cy.get('.rotation').eq(1).clear().type('90.5');
       cy.get('.horizontal').eq(1).clear().type('190.3 mm');
       cy.get('.vertical').eq(1).clear().type('190.3 mm');
         // shapes 3
       cy.get('[id="working_area_tab_shape_btn"]').click();
       cy.get('[id="shape_tab_link_star"]').click();
       cy.get('[id="quick_shape_star_radius"]').clear().type('60');
       cy.get('[id="quick_shape_star_corners"]').clear().type('8');
       cy.get('[id="quick_shape_fill"]').click();
       cy.get('[id="quick_shape_shape_done_btn"]').click();
       cy.get('.translation').eq(2).clear().type('235.0, 238.0');
       cy.get('.rotation').eq(2).clear().type('250.5');
       cy.get('.horizontal').eq(2).clear().type('225.3 mm');
       cy.get('.vertical').eq(2).clear().type('230.3 mm');
        // shapes 4
       cy.get('[id="working_area_tab_shape_btn"]').click();
       cy.get('[id="shape_tab_link_line"]').click();
       cy.get('[id="quick_shape_line_length"]').clear().type('60');
       cy.get('[id="quick_shape_fill"]').click();
       cy.get('[id="quick_shape_shape_done_btn"]').click();
       cy.get('.translation').eq(3).clear().type('135.0, 138.0');
       cy.get('.rotation').eq(3).clear().type('150.5');
       cy.get('.horizontal').eq(3).clear().type('125.3 mm');
       cy.get('.vertical').eq(3).clear().type('130.3 mm');

       cy.get('[id="laser_button"]').click();
       cy.get('[id="laserhead_focus_reminder_modal"]').find('.btn').first().click();
       cy.get('[id="laser_button"]').click();
       cy.get('.material_entry').contains('Cardboard, single wave').click();
       // cy.get('[id="material_color_8b624a"]').click();
       cy.wait(1000);
       cy.get('[id="material_thickness_1.5"]').click();
       cy.get('[id="svgtogcode_img_intensity_black"]').clear().type('95');
       cy.get('[id="svgtogcode_img_feedrate_black"]').clear().type('1500');
       cy.get('[id="parameter_assignment_show_advanced_settings_cb"]').click();
       cy.get('.passes_input').first().clear().type('2');
       cy.get('[id="parameter_assignment_pierce_time_in"]').clear().type('5');
       cy.get('[id="svgtogcode_img_line_dist"]').clear().type('0.5');
       cy.get('.checkbox-control-and-label > .controls > .checkbox > input').click({force:true});
       cy.get('[id="parameter_assignment_engraving_mode_precise_btn"]').dblclick({force:true});
       cy.get('[id="start_job_btn"]').dblclick();
       cy.wait(7000);
       cy.get('.alert-success').should('to.exist', 'Preparation done');
       cy.reload();
       cy.wait(10000);
       cy.get('[id="designlib_tab_btn"]').click();
       cy.get('[id="design_lib_filter_gcode_radio"]').click();
       cy.get('.files_template_machinecode_gcode').first().click();
       cy.get('[id="laser_button"]').click();
       cy.get('[id="laserhead_focus_reminder_modal"]').find('.btn').first().click();
       cy.logout();
    });
  });

