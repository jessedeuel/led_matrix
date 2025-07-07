from skip import Schematic, Symbol

def to_grid(gridOrigin:tuple, gridPos:tuple, scalars:tuple, offset:tuple) -> tuple:
    return ((gridOrigin[0])-(gridPos[0]*scalars[0])-offset[0],
            (gridOrigin[1])+(gridPos[1]*scalars[1])+offset[1])

def createLEDs(sch:Schematic, led:Symbol, pwr:Symbol, gnd:Symbol, numrows:int, numcols:int, charlie:bool, start_ref_count:int=1):
    '''
        Create a grid based on some symbol
    '''
    dcount = start_ref_count
    pwr_count = 3
    table = []
    
    # In mm
    diodeGridOrigin = (led.at[0], led.at[1])
    gridScalars = (27.94, 22.86)
    pwrOffset = (led.at[0] - pwr.at[0], -1*(led.at[1] - pwr.at[1]))
    gndOffset = (led.at[0] - gnd.at[0], -1*(led.at[1] - gnd.at[1]))
    
    for row in range(numrows):
        column_leds = []
        
        for col in range(numcols):
            # clone the symbol
            if not (row == 0 and col == 0):
                newD = led.clone()
                newPwr = pwr.clone()
                newGnd = gnd.clone()
                    
                # move this component where we want it, on the grid
                diode_coords = to_grid(diodeGridOrigin, (col, row), gridScalars, (0, 0))
                pwr_coords = to_grid(diodeGridOrigin, (col, row), gridScalars, pwrOffset)
                gnd_coords = to_grid(diodeGridOrigin, (col, row), gridScalars, gndOffset)
                newD.move(diode_coords[0], diode_coords[1])
                newPwr.move(pwr_coords[0], pwr_coords[1])
                newGnd.move(gnd_coords[0], gnd_coords[1])
                
                # set it's reference (all of em!)
                newD.setAllReferences(f'D{dcount}')
                newPwr.setAllReferences("#PWR%02d" % (pwr_count))
                newPwr = sch.symbol.reference_matches("#PWR%02d" % (pwr_count))[0]
                pwr_count += 1
                newGnd.setAllReferences("#PWR%02d" % (pwr_count))
                newGnd = sch.symbol.reference_matches("#PWR%02d" % (pwr_count))[0]
                pwr_count += 1
                
                # Wire ground symbol
                gnd_wire_1 = sch.wire.new()
                gnd_wire_1.start_at(newGnd.at)
                #print(f'New GND location: {newGnd.at.raw}')
                gnd_wire_1.delta_x = 0
                gnd_wire_1.delta_y = -2.54
                gnd_wire_2 = sch.wire.new()
                #print(f'Wire2 start x: {newGnd.at[0]}, y: {newD.pin.GND.location.value[1]}')
                gnd_wire_2.start_at([newD.pin.GND.location.value[0]+2.54, newD.pin.GND.location.value[1]])
                gnd_wire_2.delta_y = 0
                gnd_wire_2.delta_x = -2.54
                
                # Wire PWR symbol
                pwr_wire_1 = sch.wire.new()
                pwr_wire_1.start_at(newPwr.at)
                #print(f'New GND location: {newGnd.at.raw}')
                pwr_wire_1.delta_x = 0
                pwr_wire_1.delta_y = +2.54
                pwr_wire_2 = sch.wire.new()
                #print(f'Wire2 start x: {newGnd.at[0]}, y: {newD.pin.GND.location.value[1]}')
                pwr_wire_2.start_at([newD.pin.VDD.location.value[0]-2.54, newD.pin.VDD.location.value[1]])
                pwr_wire_2.delta_y = 0
                pwr_wire_2.delta_x = 2.54
                
                # Wire DO to DI
                digital_wire_1 = sch.wire.new()
                last_d = sch.symbol.reference_matches("D%d" % (dcount-1))[0]
                digital_wire_1.start_at([last_d.pin.DO.location.value[0], last_d.pin.DO.location.value[1]])
                digital_wire_1.delta_y = 0
                digital_wire_1.delta_x = -5*1.27
                digital_wire_2 = sch.wire.new()
                digital_wire_2.start_at([last_d.pin.DO.location.value[0]-(5*1.27), last_d.pin.DO.location.value[1]])
                digital_wire_2.delta_x = 0
                digital_wire_2.delta_y = -4*1.27
                digital_wire_3 = sch.wire.new()
                digital_wire_3.start_at([newD.pin.DI.location.value[0], newD.pin.DI.location.value[1]])
                digital_wire_3.delta_y = 0
                digital_wire_3.delta_x = 5*1.27
                
                
                # keep track of LEDs we cloned
                column_leds.append(newD)
                
            dcount += 1
        
        table.append(column_leds)
            
    return table

def createXYGrid(sch:Schematic, basedOn:Symbol, 
                      numrows:int, numcols:int, start_ref_count:int=1):
    
    column_wires = createAndWireLEDs(sch, basedOn, numrows, numcols, charlie=False, start_ref_count=start_ref_count)
    
    col_count = 0
    for join_wire in column_wires:
        # add a global label
        lbl = sch.global_label.new()
        lbl.move(join_wire.end.value[0], join_wire.end.value[1])
        lbl.value = f'COL_{col_count+1}'
        col_count += 1
        
    
    print(f'Done: created a {numrows}x{numcols} grid')

if __name__ == "__main__":
    schem_file = "../led_matrix.kicad_sch"
    schematic = Schematic(schem_file)
    
    diodes = schematic.symbol.reference_startswith('D')
    pwr = schematic.symbol.PWR01
    gnd = schematic.symbol.PWR02
    
    createLEDs(schematic, diodes[0], pwr, gnd, 16, 16, len(diodes))
    
    schematic.write(schem_file)