import h3


def generate_kml(hexagons):
    """
    Генерирует KML-строку из списка гексагонов с их level и cell_id.
    Args:
        hexagons: Список кортежей [h3_index, level, cell_id]
    Returns:
        KML-документ в виде строки
    """
    header = """<?xml version="1.0" encoding="UTF-8"?>
                <kml xmlns="http://www.opengis.net/kml/2.2">
                <Document>
                    <name>H3 Hexagons inside polygon</name>
                    <Style id="hexStyle">
                        <LineStyle>
                            <color>ff0000ff</color>
                            <width>2</width>
                        </LineStyle>
                        <PolyStyle>
                            <color>400000ff</color>
                            <fill>1</fill>
                            <outline>1</outline>
                        </PolyStyle>
                    </Style>
                """
    footer = "</Document>\n</kml>"
    placemarks = []
    for h3_idx, level, cell_id in hexagons:
        boundary = h3.cell_to_boundary(h3_idx)
        coords_parts = [f"{lon},{lat},0" for lat, lon in boundary]
        coords = " ".join(coords_parts)
        coords += f" {boundary[0][1]},{boundary[0][0]},0"
        placemark = f"""<Placemark>
                            <name>{h3_idx}</name>
                            <description>level: {level}, cell_id: {cell_id}</description>
                            <styleUrl>#hexStyle</styleUrl>
                            <Polygon>
                                <tessellate>1</tessellate>
                                <outerBoundaryIs>
                                    <LinearRing>
                                        <coordinates>{coords}</coordinates>
                                    </LinearRing>
                                </outerBoundaryIs>
                            </Polygon>
                        </Placemark>
                    """
        placemarks.append(placemark)
    return header + "\n".join(placemarks) + footer
