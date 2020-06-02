import bitstring


class CacheParser:
    @staticmethod
    def parse_from(data):
        bit_data = bitstring.Bits(data)
        # current_index = 0
        header = CacheParser.parse_header(bit_data)
        current_index = 96
        queries = []
        answers = []
        authority_answers = []
        additional_answers = []
        for i in range(header["Questions"]):
            query, index = CacheParser.parse_query(bit_data, current_index)
            queries.append(query)
            current_index = index
        for i in range(header["Answers"]):
            answer, index = CacheParser.parse_answer(bit_data, current_index)
            answers.append(answer)
            current_index = index
        for i in range(header["Authority"]):
            authority_answer, index = CacheParser.parse_answer(bit_data, current_index)
            authority_answers.append(authority_answer)
            current_index = index
        for i in range(header["Additional"]):
            additional_answer, index = CacheParser.parse_answer(bit_data, current_index)
            additional_answers.append(additional_answer)
            current_index = index
        return header, queries, answers, authority_answers, additional_answers

    @staticmethod
    def parse_name(data: bitstring.Bits, current_index: int):
        name = ""
        length = data[current_index:current_index + 8].uint
        while length != 0:
            if length < 192:
                current_index += 8
                name += str(data[current_index:current_index + length * 8].bytes, "ASCII") + "."
                current_index += length * 8
            else:
                jump = data[current_index + 2:current_index + 16].uint * 8
                name += CacheParser.parse_name(data, jump)[0]
                return name, current_index + 16
            length = data[current_index:current_index + 8].uint
        return name[:-1], current_index + 8

    @staticmethod
    def parse_header(data: bitstring.Bits):
        return {"TransactionID": data[0:16].uint,
                "Qr": data[16:17].uint,
                "Opcode": data[17:21].uint,
                "Authoritative": data[21:22].uint,
                "Truncated": data[22:23].uint,
                "Recursion_desired": data[23:24].uint,
                "Recursion_available": data[24:25].uint,
                "Reply_code": data[28:32].uint,
                "Questions": data[32:48].uint,
                "Answers": data[48:64].uint,
                "Authority": data[64:80].uint,
                "Additional": data[80:96].uint}

    @staticmethod
    def parse_query(data: bitstring.Bits, current_index: int):
        name, index = CacheParser.parse_name(data, current_index)
        return ({"Name": name,
                 "Type": data[index:index + 16].uint,
                 "Class": data[index + 16:index + 32].uint}, index + 32)

    @staticmethod
    def parse_answer(data: bitstring.Bits, current_index: int):
        name, index = CacheParser.parse_name(data, current_index)
        qtype = data[index:index + 16].uint
        address_length = data[index + 64:index + 80].uint
        address, final_index = CacheParser.parse_address(data, index + 80, address_length, qtype)
        return ({"Name": name,
                 "Type": qtype,
                 "Class": data[index + 16:index + 32].uint,
                 "TTL": data[index + 32:index + 64].uint,
                 "Length": address_length,
                 "Address": address}, final_index)

    @staticmethod
    def parse_address(data: bitstring.Bits, index: int, length: int, qtype: int):
        if qtype == 1:
            address = ""
            for i in range(length):
                address += str(data[index:index + 8].uint) + "."
                index = index + 8
            return address[:-1], index
        elif qtype == 2:
            name, index = CacheParser.parse_name(data, index)[0], index + 8 * length
            return name, index

    @staticmethod
    def parse_to(data, results):
        resulted = bitstring.BitArray().bytes
        resulted += CacheParser.parse_header_to(data, results)
        for query in data[1]:
            resulted += CacheParser.parse_query_to(query)
        for query in data[1]:
            for result in results[0]:
                resulted += CacheParser.parse_answer_to(query, result)
        return resulted

    @staticmethod
    def parse_header_to(data, results):
        header, queries, answers, authority_answers, additional_answers = data
        header_format = "uint:16, uint:1, uint:4, uint:1, uint:1, uint:1, uint:1, uint:3, uint:4, uint:16, uint:16, " \
                        "uint:16, uint:16"
        return bitstring.pack(header_format, header["TransactionID"],
                              1, header["Opcode"], header["Authoritative"],
                              header["Truncated"], header["Recursion_desired"],
                              0, 0, 0, len(queries), len(results[0]),
                              len(authority_answers), len(additional_answers)).bytes

    @staticmethod
    def parse_answer_to(query, result):
        resulted = bitstring.BitArray()
        name, _ = CacheParser.parse_name_to(query["Name"])
        resulted += name
        if query["Type"] == 1:
            name_addr = CacheParser.parse_address_to(result[2])
            length = 4
        else:
            name_addr, length = CacheParser.parse_name_to(result[2])
        answer_format = "uint:16, uint:16, uint:32, uint:16"
        resulted += bitstring.pack(answer_format, query["Type"], query["Class"], result[0], length)
        resulted += name_addr
        return resulted.bytes

    @staticmethod
    def parse_query_to(query):
        result = bitstring.BitArray()
        name, _ = CacheParser.parse_name_to(query["Name"])
        result += name
        result += bitstring.pack("uint:16, uint:16", query["Type"], query["Class"])
        return result.bytes

    @staticmethod
    def parse_name_to(name: str):
        length = 0
        result = bitstring.BitArray()
        for part in name.split("."):
            result += bitstring.pack("uint:8", len(part))
            length += len(part) + 1
            for char in part:
                result += bitstring.pack("hex:8", char.encode("ASCII").hex())
        result += bitstring.pack("uint:8", 0)
        length += 1
        return result.bytes, length

    @staticmethod
    def parse_address_to(address: str):
        result = bitstring.BitArray()
        for part in address.split("."):
            result += bitstring.pack("uint:8", int(part))
        return result.bytes
