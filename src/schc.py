"""
.. module:: schc
   :platform: Python, Micropython
"""
# ---------------------------------------------------------------------------

from base_import import *  # used for now for differing modules in py/upy

# ---------------------------------------------------------------------------

from schcrecv import ReassemblerAckOnError
from schcrecv import ReassemblerNoAck
from schcsend import FragmentAckOnError
from schcsend import FragmentNoAck
import schcmsg
from comp_parser import *
from schccomp import Compressor, Decompressor

class Session:
    """ fragmentation/reassembly session manager
    session = [
        { "ruleID": n, "ruleLength", "dtag": n, "session": session }, ...
        ]
    """
    def __init__(self, protocol):
        self.protocol = protocol
        self.session_list = []

    def add(self, rule_id, rule_id_size, dtag, session):
        if self.get(rule_id, rule_id_size, dtag) is not None:
            print("ERROR: the session rid={}/{} dtag={} exists already".format(
                    rule_id, rule_id_size, dtag))
            return False
        self.session_list.append({"rule_id": rule_id,
                                  "rule_id_size": rule_id_size, "dtag": dtag,
                                  "session": session })
        return True

    def get(self, rule_id, rule_id_size, dtag):
        for i in self.session_list:
            if (rule_id == i["rule_id"] and
                rule_id_size == i["rule_id_size"] and dtag == i["dtag"]):
                return i["session"]
        return None

class SCHCProtocol:
    """This class is the entry point for the openschc
    (in this current form, object composition is used)"""
    #def __init__(self, config, scheduler, schc_layer2, role="sender"):
    def __init__(self, config, system, layer2, layer3):
        self.config = config
        self.system = system
        self.scheduler = system.get_scheduler()
        self.layer2 = layer2
        self.layer3 = layer3
        self.layer2._set_protocol(self)
        self.layer3._set_protocol(self)
        self.default_frag_rule = None # XXX: to be in  rule_manager
        self.compressor = Compressor(self)
        self.decompressor = Decompressor(self)
        self.fragment_session = Session(self)
        self.reassemble_session = Session(self)

    def _log(self, message):
        self.log("schc", message)

    def log(self, name, message):
        self.system.log(name, message)

    def set_rulemanager(self, rule_manager):
        self.rule_manager = rule_manager

    def schc_send(self, dst_L3addr, raw_packet):
        self._log("recv-from-L3 -> {} {}".format(dst_L3addr, raw_packet))
        context = self.rule_manager.find_context_bydstiid(dst_L3addr)
<<<<<<< HEAD
        if context is None:
            # reject it.
            self._log("Rejected. Not for SCHC packet, L3addr={}".format(
                    dst_L3addr))
            return
        # Compression process
        packet_bbuf = BitBuffer(raw_packet)
        if not self.config.get("debug-fragment"):
            print("----------------------- Compression Process ----------------------------")
            # XXX debug_protocol is for debug, need to be moved somewhere.
            class debug_protocol:
                def _log(*arg):
                    print(*arg)
            p = Parser(debug_protocol)
            # XXX a hint of the direction must be defined in the config.
            direction = T_DIR_UP    # XXX must be defined in the config or other!!
            v = p.parse(raw_packet, direction)
            self._log("packet parsed: {}".format(pprint.pprint(v[0])))
            rule = self.rule_manager.FindRuleFromPacket(v[0], direction=direction)
            if rule != None:
                self._log("compression rule={}".format(rule))
                schc_packet = self.compressor.compress(rule, v[0], v[1], direction)
                #NEED TO BE FIX -> there is an error when packets are larger than 250B
                #The assert in the funcion __add__ of bitarray.py line 257 gives an 
                #Assertion Error.
                # check if fragmentation is needed.
                if packet_bbuf.count_added_bits() < self.layer2.get_mtu_size():
                    self._log("SCHC fragmentation is not needed. size={}".format(
                            packet_bbuf.count_added_bits()))
                    args = (packet_bbuf.get_content(), context["devL2Addr"])
                    self.scheduler.add_event(0, self.layer2.send_packet, args)
                    return
            
        # fragmentation is required.

        # NOTE: If you need fragmentation just after compression, the follwing
        # fragmentation block should be included in the above "comp" block.

        # Do fragmenation
        print("----------------------- Fragmentation Rule -----------------------")
        rule = context["fragSender"]
        pprint.pprint(rule.__dict__)
        self._log("fragmentation rule_id={}".format(rule.RuleID))
=======
        print ("raw_packet", raw_packet)
 
        P = Parser(debug_protocol)
        
        try:
            parsed_packet = P.parse(raw_packet, T_DIR_UP)
            pprint.pprint(parsed_packet[0])
        except: 
            print ("no parsing, try fragmentation")
            parsed_packet = None
            schc_packet = None
 
        if parsed_packet != None:
            #pass        # to be done            
            rule = self.rule_manager.FindRuleFromPacket(parsed_packet[0], direction="UP")
            if rule is None:
                # reject it.
                self._log("Rejected. Not for SCHC packet, L3addr={}".format(
                        dst_L3addr))
                return
            # Compression process
            #packet_bbuf = BitBuffer(raw_packet)
            #rule = rule["Compression"]
            #C = Compressor(debug_protocol)
            print ("selected rule is ", rule)            
        #self._log("ompression rule_id={}".format(rule.ruleID))
        # XXX needs to handl the direction
        #packet_bbuf = self.compressor.compress(context, packet_bbuf)
        print("-------------------------------------- Compression Proccess -------------------------------------------")
        schc_packet = self.compressor.compress(rule, parsed_packet[0], parsed_packet[1], T_DIR_UP)
        
        print (schc_packet)        
        schc_packet.display("bin")

        if schc_packet == None:
            packet_bbuf = BitBuffer(raw_packet)
        else:
            packet_bbuf = schc_packet

        # check if fragmentation is needed.
        if packet_bbuf.count_added_bits() < self.layer2.get_mtu_size():
            self._log("SCHC fragmentation is not needed. size={}".format(
                    packet_bbuf.count_added_bits()))
            """ Changement à corriger
            args = (packet_bbuf.get_content(), context["devL2Addr"])
            """
            args = (packet_bbuf.get_content(), "*")
            self.scheduler.add_event(0, self.layer2.send_packet, args)
            return

        # fragmentation is required.
        frag_rule = self.rule_manager.FindFragmentationRule(self.layer2.devaddr)        
        if frag_rule is None:
            self._log("Rejected the packet due to no fragmenation rule.")
            return
        # Do fragmenation
        print("-------------------------------------- Fragmentation Proccess -------------------------------------------")
        rule = frag_rule
        context = None # LT: don't know why context is needed, should be self.rule_manager which handle the context
        self._log("fragmentation rule_id={}".format(rule[T_RULEID]))
>>>>>>> 84256f7... Compression, fragmentation and rulemanager
        session = self.new_fragment_session(context, rule)
        session.set_packet(packet_bbuf)
        self.fragment_session.add(rule.RuleID, rule.RuleIDLength,
                                    session.dtag, session)
        session.start_sending()

    def new_fragment_session(self, context, rule):
        mode = rule[T_FRAG][T_FRAG_MODE]
        if mode == "noAck":
            session = FragmentNoAck(self, context, rule) # XXX
        elif mode == "ackAlwayw":
            raise NotImplementedError(
                    "{} is not implemented yet.".format(mode))
        elif mode == "ackOnError":
            session = FragmentAckOnError(self, context, rule) # XXX
        else:
            raise ValueError("invalid FRMode: {}".format(mode))
        return session

    def new_reassemble_session(self, context, rule, dtag, dev_L2addr):
        mode = rule.get("FRMode")
        if mode == "noAck":
            session = ReassemblerNoAck(self, context, rule, dtag, dev_L2addr)
        elif mode == "ackAlways":
            raise NotImplementedError("FRMode:", mode)
        elif mode == "ackOnError":
            session = ReassemblerAckOnError(self, context, rule, dtag,
                                            dev_L2addr)
        else:
            raise ValueError("FRMode:", mode)
        return session

    def schc_recv(self, dev_L2addr, raw_packet):
<<<<<<< HEAD
        self._log("recv-from-L2 {} {}".format(dev_L2addr, raw_packet))
        # find context for the SCHC processing.
        # XXX
        # the receiver never knows if the packet from the device having the L2
        # addrss is encoded in SCHC.  Therefore, it has to search the db with
        # the field value of the packet.
        context = self.rule_manager.find_context_bydevL2addr(dev_L2addr)
        if context is None:
            # reject it.
            self._log("Rejected. Not for SCHC packet, sender L2addr={}".format(
                    dev_L2addr))
            return
        # find a rule in the context for this packet.
        packet_bbuf = BitBuffer(raw_packet) 
        #XXX print(self.rule_manager.FindRuleFromSCHCpacket(packet_bbuf))
        key, rule = self.rule_manager.find_rule_bypacket(context, packet_bbuf)
        print('key,rule {},{}'.format(key,rule))

        if key == "fragSender":
            schc_frag = schcmsg.frag_sender_rx(rule, packet_bbuf)
            # find existing session for fragment or reassembly.
            session = self.fragment_session.get(rule.RuleID,
                                                rule.RuleIDLength,
                                                schc_frag.dtag)
            print("rule.ruleID -> {},rule.ruleLength-> {}, dtag -> {}".format(
                rule.RuleID, rule.RuleIDLength, schc_frag.dtag))
            if session is not None:
                print("Fragmentation session found", session)
                session.receive_frag(schc_frag)
            else:
                print("context exists, but no {} session for this packet {}".
                        format(key, dev_L2addr))
        elif key == "fragReceiver":
            schc_frag = schcmsg.frag_receiver_rx(rule, packet_bbuf)
            # find existing session for fragment or reassembly.
            session = self.reassemble_session.get(rule.RuleID,
                                                rule.RuleIDLength, schc_frag.dtag)
            print("rule.RuleID -> {},rule.RuleIDLength-> {}, dtag -> {}".format(
                    rule.RuleID,rule.RuleIDLength, schc_frag.dtag))
            
            if session is not None:
                print("Reassembly session found", session)
            else:
                # no session is found.  create a new reassemble session.
                session = self.new_reassemble_session(context, rule, schc_frag.dtag,
                                                      dev_L2addr)
                self.reassemble_session.add(rule.RuleID, rule.RuleIDLength,
                                            schc_frag.dtag, session)
                print("New reassembly session created", session)
            print("----------------------- Reassembly process -----------------------")
            session.receive_frag(schc_frag)
        #
        rule = self.rule_manager.FindRuleFromSCHCpacket(schc=packet_bbuf)
        if rule is not None:
            # if there is no reassemble rule, process_decompress() is directly
            # called from here.  Otherwise, it will be called from a reassemble
            # function().
            self.process_decompress(rule, dev_L2addr, packet_bbuf)

    def process_decompress(self, rule, dev_L2addr, schc_packet):
        if rule is not None:
            self._log("compression rule_id={}".format(rule))
            direction = T_DIR_UP    # XXX it must come from the config!!!
            raw_packet = self.decompressor.decompress(schc_packet, rule, direction=T_DIR_UP)
        else:
            raw_packet = schc_packet
        args = (dev_L2addr, raw_packet)
        self.scheduler.add_event(0, self.layer3.recv_packet, args)
=======
        # self._log("recv-from-L2 {} {}".format(dev_L2addr, raw_packet))

        frag_rule = self.rule_manager.FindFragmentationRule(dev_L2addr)

        # print(dev_L2addr)
        packet_bbuf = BitBuffer(raw_packet)
        # print("raw_packet", raw_packet)
        # print("schc packet", packet_bbuf)
        # print("frag_rule", frag_rule)

        # !IMPORTANT: This condition has to be changed by a context condition like in the last version
        if dev_L2addr == b"\xaa\xbb\xcc\xee":

            if frag_rule[T_FRAG][T_FRAG_PROF][T_FRAG_DTAG] > 0:
                dtag = packet_bbuf.get_bits(frag_rule[T_FRAG][T_FRAG_PROF][T_FRAG_DTAG],
                                    position=frag_rule[T_RULEIDLENGTH])
            else:
                dtag = None

            # find existing session for fragment or reassembly.
            session = self.reassemble_session.get(frag_rule[T_RULEID], frag_rule[T_RULEIDLENGTH], dtag)
            if session is not None:
                print("Reassembly session found", session)
            else:
                # no session is found.  create a new reassemble session.
                context = None
                session = self.new_reassemble_session(context, frag_rule, dtag,
                                                        dev_L2addr)
                self.reassemble_session.add(frag_rule[T_RULEID], frag_rule[T_RULEIDLENGTH],
                                            dtag, session)
                print("New reassembly session created", session)
            session.receive_frag(packet_bbuf, dtag)
            return

            self.process_decompress(packet_bbuf, dev_L2addr, direction= T_DIR_UP)

        elif dev_L2addr == b"\xaa\xbb\xcc\xdd":
            if frag_rule[T_FRAG][T_FRAG_PROF][T_FRAG_DTAG] > 0:
                dtag = packet_bbuf.get_bits(frag_rule[T_FRAG][T_FRAG_PROF][T_FRAG_DTAG],
                                    position=frag_rule[T_RULEIDLENGTH])
            else:
                dtag = None
            # find existing session for fragment or reassembly.
            session = self.fragment_session.get(frag_rule[T_RULEID], frag_rule[T_RULEIDLENGTH], dtag)
            print("rule.ruleID -> {},rule.ruleLength-> {}, dtag -> {}".format(frag_rule[T_RULEID],frag_rule[T_RULEIDLENGTH], dtag))
            if session is not None:
                print("Fragmentation session found", session)
                session.receive_frag(packet_bbuf, dtag)
            else:
                print("context exists, but no {} session for this packet {}".
                        format(dev_L2addr))
            return



    # def schc_recv(self, dev_L2addr, raw_packet):
    #     self._log("recv-from-L2 {} {}".format(dev_L2addr, raw_packet))
    #     # find context for the SCHC processing.
    #     # XXX
    #     # the receiver never knows if the packet from the device having the L2
    #     # addrss is encoded in SCHC.  Therefore, it has to search the db with
    #     # the field value of the packet.
    #     context = self.rule_manager.find_context_bydevL2addr(dev_L2addr)
    #     if context is None:
    #         # reject it.
    #         self._log("Rejected. Not for SCHC packet, sender L2addr={}".format(
    #                 dev_L2addr))
    #         return
    #     # find a rule in the context for this packet.
    #     packet_bbuf = BitBuffer(raw_packet)
    #     key, rule = self.rule_manager.find_rule_bypacket(context, packet_bbuf)
    #     if key == "fragSender":
    #         if rule["dtagSize"] > 0:
    #             dtag = packet_bbuf.get_bits(rule.get("dtagSize"),
    #                                 position=rule.get("ruleLength"))
    #         else:
    #             dtag = None
    #         # find existing session for fragment or reassembly.
    #         session = self.fragment_session.get(rule.ruleID,
    #                                             rule.ruleLength, dtag)
    #         if session is not None:
    #             print("Fragmentation session found", session)
    #             session.receive_frag(packet_bbuf, dtag)
    #         else:
    #             print("context exists, but no {} session for this packet {}".
    #                     format(key, dev_L2addr))
    #     elif key == "fragReceiver":
    #         if rule["dtagSize"] > 0:
    #             dtag = packet_bbuf.get_bits(rule.get("dtagSize"),
    #                                 position=rule.get("ruleLength"))
    #         else:
    #             dtag = None
    #         # find existing session for fragment or reassembly.
    #         session = self.reassemble_session.get(rule.ruleID,
    #                                             rule.ruleLength, dtag)
    #         if session is not None:
    #             print("Reassembly session found", session)
    #         else:
    #             # no session is found.  create a new reassemble session.
    #             session = self.new_reassemble_session(context, rule, dtag,
    #                                                   dev_L2addr)
    #             self.reassemble_session.add(rule.ruleID, rule.ruleLength,
    #                                         dtag, session)
    #             print("New reassembly session created", session)
    #         session.receive_frag(packet_bbuf, dtag)
    #     elif key == "comp":
    #         # if there is no reassemble rule, process_decompress() is directly
    #         # called from here.  Otherwise, it will be called from a reassemble
    #         # function().
    #         self.process_decompress(context, dev_L2addr, packet_bbuf)
    #     elif key is None:
    #         raise ValueError(
    #                 "context exists, but no rule found for L2Addr {}".
    #                 format(dev_L2addr))
    #     else:
    #         raise SystemError("should not come here.")        

    def process_decompress(self, packet_bbuf, dev_L2addr, direction):
        rule = self.rule_manager.FindRuleFromSCHCpacket(packet_bbuf,dev_L2addr)
        if rule is None:
            # reject it.
            self._log("Rejected. Not for SCHC packet, sender L2addr={}".format(
                    dev_L2addr))
            return
        print("---------------------- Decompression Process----------------------")
        print("---------------------- Decompression Rule-------------------------")
        self._log("compression rule_id={}".format(rule[T_RULEID]))
        # print('rule {}'.format(rule))
        print("------------------------ Decompression ---------------------------")
        raw_packet = self.decompressor.decompress(packet_bbuf, rule, direction)
        print("---- Decompression result ----")
        print(raw_packet)
        args = (dev_L2addr, raw_packet)
        self.scheduler.add_event(0, self.layer3.recv_packet, args)

    #def process_decompress(self, context, dev_L2addr, schc_packet):
    #    self._log("compression rule_id={}".format(context["comp"]["ruleID"]))
    #    raw_packet = self.decompressor.decompress(context, schc_packet)
    #    args = (dev_L2addr, raw_packet)
    #    self.scheduler.add_event(0, self.layer3.recv_packet, args)
>>>>>>> 84256f7... Compression, fragmentation and rulemanager
